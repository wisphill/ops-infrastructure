FROM golang:1.27 AS build
WORKDIR /src
COPY backend/go.mod backend/go.sum ./
RUN go mod download
COPY backend/ ./
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /portal .

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /portal /portal
COPY web/ /web/
ENV WEB_DIR=/web LISTEN_ADDR=:8080
EXPOSE 8080
ENTRYPOINT ["/portal"]
