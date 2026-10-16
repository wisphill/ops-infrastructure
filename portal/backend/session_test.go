package main

import (
	"testing"
	"time"
)

func TestSignerRoundTrip(t *testing.T) {
	s := signer{key: []byte("0123456789abcdef0123456789abcdef")}
	tok, err := s.encode(purposeSession, user{Email: "a@gmail.com"}, time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	var u user
	if err := s.decode(purposeSession, tok, &u); err != nil || u.Email != "a@gmail.com" {
		t.Fatalf("decode = %v, %+v", err, u)
	}
}

func TestSignerRejects(t *testing.T) {
	s := signer{key: []byte("0123456789abcdef0123456789abcdef")}
	other := signer{key: []byte("fedcba9876543210fedcba9876543210")}
	valid, _ := s.encode(purposeSession, user{Email: "a@gmail.com"}, time.Minute)
	expired, _ := s.encode(purposeSession, user{}, -time.Second)
	foreign, _ := other.encode(purposeSession, user{}, time.Minute)
	login, _ := s.encode(purposeLogin, loginState{}, time.Minute)

	cases := map[string]string{
		"tampered":      "x" + valid,
		"no signature":  valid[:len(valid)-44],
		"expired":       expired,
		"wrong key":     foreign,
		"wrong purpose": login,
		"empty":         "",
	}
	for name, tok := range cases {
		var u user
		if err := s.decode(purposeSession, tok, &u); err == nil {
			t.Errorf("%s: expected error", name)
		}
	}
}
