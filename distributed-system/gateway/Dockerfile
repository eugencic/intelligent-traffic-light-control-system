FROM golang:1.20

WORKDIR /app

COPY Dockerfile .
COPY go.mod .
COPY go.sum .
COPY main.go .

COPY gen/ /app/gen/

COPY proto/ /app/proto/

# COPY req/ /app/req/

COPY tools/ /app/tools/

RUN go mod download

RUN go build -o gateway

EXPOSE 6060

CMD ["./gateway"]
