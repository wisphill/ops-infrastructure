package main

import (
	"crypto/subtle"
	"log"
	"net/http"
	"net/url"
	"time"

	"github.com/coreos/go-oidc/v3/oidc"
	"golang.org/x/oauth2"
)

const (
	sessionCookie  = "portal_session"
	loginCookie    = "portal_login"
	purposeSession = "session"
	purposeLogin   = "login"
	sessionTTL     = 8 * time.Hour
	loginTTL       = 10 * time.Minute
)

type user struct {
	Sub     string `json:"sub"`
	Email   string `json:"email"`
	Name    string `json:"name"`
	Picture string `json:"picture"`
}

type loginState struct {
	State    string `json:"state"`
	Nonce    string `json:"nonce"`
	Verifier string `json:"verifier"`
}

type auth struct {
	oauth    *oauth2.Config
	verifier *oidc.IDTokenVerifier
	signer   signer
	secure   bool
}

func (a *auth) setCookie(w http.ResponseWriter, name, value string, ttl time.Duration) {
	http.SetCookie(w, &http.Cookie{
		Name:     name,
		Value:    value,
		Path:     "/",
		MaxAge:   int(ttl.Seconds()),
		HttpOnly: true,
		Secure:   a.secure,
		SameSite: http.SameSiteLaxMode,
	})
}

func (a *auth) clearCookie(w http.ResponseWriter, name string) {
	http.SetCookie(w, &http.Cookie{
		Name:     name,
		Value:    "",
		Path:     "/",
		MaxAge:   -1,
		HttpOnly: true,
		Secure:   a.secure,
		SameSite: http.SameSiteLaxMode,
	})
}

func (a *auth) currentUser(r *http.Request) (user, bool) {
	var u user
	c, err := r.Cookie(sessionCookie)
	if err != nil || a.signer.decode(purposeSession, c.Value, &u) != nil {
		return user{}, false
	}
	return u, true
}

func (a *auth) login(w http.ResponseWriter, r *http.Request) {
	st := loginState{State: randomToken(), Nonce: randomToken(), Verifier: oauth2.GenerateVerifier()}
	val, err := a.signer.encode(purposeLogin, st, loginTTL)
	if err != nil {
		http.Error(w, "internal error", http.StatusInternalServerError)
		return
	}
	a.setCookie(w, loginCookie, val, loginTTL)

	target := a.oauth.AuthCodeURL(st.State,
		oidc.Nonce(st.Nonce),
		oauth2.S256ChallengeOption(st.Verifier),
		oauth2.SetAuthURLParam("prompt", "select_account"),
	)
	http.Redirect(w, r, target, http.StatusFound)
}

func (a *auth) callback(w http.ResponseWriter, r *http.Request) {
	var st loginState
	c, err := r.Cookie(loginCookie)
	if err != nil || a.signer.decode(purposeLogin, c.Value, &st) != nil {
		redirectWithError(w, r, "login_expired")
		return
	}
	a.clearCookie(w, loginCookie)

	q := r.URL.Query()
	if e := q.Get("error"); e != "" {
		redirectWithError(w, r, e)
		return
	}
	if subtle.ConstantTimeCompare([]byte(q.Get("state")), []byte(st.State)) != 1 {
		redirectWithError(w, r, "invalid_state")
		return
	}

	tok, err := a.oauth.Exchange(r.Context(), q.Get("code"), oauth2.VerifierOption(st.Verifier))
	if err != nil {
		log.Printf("code exchange failed: %v", err)
		redirectWithError(w, r, "exchange_failed")
		return
	}
	rawIDToken, ok := tok.Extra("id_token").(string)
	if !ok {
		redirectWithError(w, r, "missing_id_token")
		return
	}

	// Verify checks the RS256 signature against Google's JWKS, plus iss, aud (our client ID) and exp.
	idToken, err := a.verifier.Verify(r.Context(), rawIDToken)
	if err != nil {
		log.Printf("id token verification failed: %v", err)
		redirectWithError(w, r, "invalid_id_token")
		return
	}
	if subtle.ConstantTimeCompare([]byte(idToken.Nonce), []byte(st.Nonce)) != 1 {
		redirectWithError(w, r, "invalid_nonce")
		return
	}

	var claims struct {
		Email         string `json:"email"`
		EmailVerified bool   `json:"email_verified"`
		Name          string `json:"name"`
		Picture       string `json:"picture"`
	}
	if err := idToken.Claims(&claims); err != nil || !claims.EmailVerified {
		redirectWithError(w, r, "email_not_verified")
		return
	}

	u := user{Sub: idToken.Subject, Email: claims.Email, Name: claims.Name, Picture: claims.Picture}
	val, err := a.signer.encode(purposeSession, u, sessionTTL)
	if err != nil {
		http.Error(w, "internal error", http.StatusInternalServerError)
		return
	}
	a.setCookie(w, sessionCookie, val, sessionTTL)
	log.Printf("login: %s", u.Email)
	http.Redirect(w, r, "/home", http.StatusFound)
}

func (a *auth) logout(w http.ResponseWriter, r *http.Request) {
	a.clearCookie(w, sessionCookie)
	http.Redirect(w, r, "/", http.StatusSeeOther)
}

func redirectWithError(w http.ResponseWriter, r *http.Request, code string) {
	http.Redirect(w, r, "/?error="+url.QueryEscape(code), http.StatusFound)
}
