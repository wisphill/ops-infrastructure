package main

import (
	"crypto/hmac"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"errors"
	"strings"
	"time"
)

var errInvalidToken = errors.New("invalid or expired token")

// signer produces tamper-proof cookie values: base64url(payload) "." base64url(HMAC-SHA256).
// The purpose is mixed into the MAC so a value minted for one cookie cannot be replayed as another.
type signer struct {
	key []byte
}

type envelope struct {
	Exp  int64           `json:"exp"`
	Data json.RawMessage `json:"data"`
}

func (s signer) mac(purpose, payload string) []byte {
	m := hmac.New(sha256.New, s.key)
	m.Write([]byte(purpose + "." + payload))
	return m.Sum(nil)
}

func (s signer) encode(purpose string, v any, ttl time.Duration) (string, error) {
	data, err := json.Marshal(v)
	if err != nil {
		return "", err
	}
	raw, err := json.Marshal(envelope{Exp: time.Now().Add(ttl).Unix(), Data: data})
	if err != nil {
		return "", err
	}
	payload := base64.RawURLEncoding.EncodeToString(raw)
	return payload + "." + base64.RawURLEncoding.EncodeToString(s.mac(purpose, payload)), nil
}

func (s signer) decode(purpose, token string, v any) error {
	payload, sig, ok := strings.Cut(token, ".")
	if !ok {
		return errInvalidToken
	}
	got, err := base64.RawURLEncoding.DecodeString(sig)
	if err != nil || !hmac.Equal(got, s.mac(purpose, payload)) {
		return errInvalidToken
	}
	raw, err := base64.RawURLEncoding.DecodeString(payload)
	if err != nil {
		return errInvalidToken
	}
	var env envelope
	if err := json.Unmarshal(raw, &env); err != nil || time.Now().Unix() >= env.Exp {
		return errInvalidToken
	}
	return json.Unmarshal(env.Data, v)
}

func randomToken() string {
	b := make([]byte, 32)
	if _, err := rand.Read(b); err != nil {
		panic(err)
	}
	return base64.RawURLEncoding.EncodeToString(b)
}
