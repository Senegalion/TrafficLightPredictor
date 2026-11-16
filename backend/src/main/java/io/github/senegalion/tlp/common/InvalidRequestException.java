package io.github.senegalion.tlp.common;

/** A syntactically valid request that violates a business rule. */
public class InvalidRequestException extends RuntimeException {

    public InvalidRequestException(String message) {
        super(message);
    }
}
