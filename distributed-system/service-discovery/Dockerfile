FROM golang:1.20

WORKDIR /app

COPY go.mod go.sum ./
COPY main.go .

RUN go mod download

RUN go build -o service-discovery

EXPOSE 9090

CMD ["./service-discovery"]
