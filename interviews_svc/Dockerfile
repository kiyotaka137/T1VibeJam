FROM golang:1.23-alpine AS build
WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /bin/server ./cmd/server

FROM alpine:3.20
RUN adduser -D -H -s /sbin/nologin appuser
COPY --from=build /bin/server /server
USER appuser
EXPOSE 8080
ENTRYPOINT ["/server"]
