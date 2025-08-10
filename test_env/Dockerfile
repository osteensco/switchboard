
# build stage
FROM golang:1.24-alpine AS builder

WORKDIR /app/cli/src

COPY ./cli/src/go.mod ./cli/src/go.sum ./

RUN go mod download

COPY ./cli/src ./

RUN go build -o /usr/local/bin/sb ./main.go



# runtime stage
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    bash git python3 python3-pip curl unzip groff less \
    && apt-get clean

ENV TERRAFORM_VERSION=1.8.4

RUN curl -fsSL https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip \
    -o terraform.zip && \
    unzip terraform.zip && \
    mv terraform /usr/local/bin/ && \
    chmod +x /usr/local/bin/terraform && \
    rm terraform.zip

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf aws awscliv2.zip

COPY --from=builder /usr/local/bin/sb /usr/local/bin/sb

ENTRYPOINT ["/bin/bash"]
