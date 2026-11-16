package io.github.senegalion.tlp.support;

import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.context.annotation.Bean;
import org.testcontainers.postgresql.PostgreSQLContainer;
import org.testcontainers.utility.DockerImageName;

/** PostgreSQL + PostGIS in Docker for repository and integration tests. */
@TestConfiguration(proxyBeanMethods = false)
public class PostgisTestcontainersConfig {

    private static final String DEFAULT_IMAGE = "imresamu/postgis:17-3.5";

    @Bean
    @ServiceConnection
    PostgreSQLContainer postgisContainer() {
        String image = System.getProperty("tlp.test.postgis-image", DEFAULT_IMAGE);
        return new PostgreSQLContainer(DockerImageName.parse(image).asCompatibleSubstituteFor("postgres"));
    }
}
