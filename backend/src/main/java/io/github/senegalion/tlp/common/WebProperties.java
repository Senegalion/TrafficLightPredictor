package io.github.senegalion.tlp.common;

import java.util.List;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;

/**
 * @param ingestionApiKey shared key required for POSTing observations; blank disables the check
 * @param corsAllowedOrigins browser origins allowed to call the API (e.g. the Vite dev server)
 */
@ConfigurationProperties("tlp.web")
public record WebProperties(String ingestionApiKey, @DefaultValue("http://localhost:5173") List<String> corsAllowedOrigins) {}
