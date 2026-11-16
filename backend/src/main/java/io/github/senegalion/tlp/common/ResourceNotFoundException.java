package io.github.senegalion.tlp.common;

public class ResourceNotFoundException extends RuntimeException {

    public ResourceNotFoundException(String resource, Object id) {
        super("%s %s was not found".formatted(resource, id));
    }
}
