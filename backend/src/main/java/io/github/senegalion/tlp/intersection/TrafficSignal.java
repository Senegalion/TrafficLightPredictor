package io.github.senegalion.tlp.intersection;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

/** A vehicle signal group at an intersection (one or more signal heads that always show the same phase). */
@Entity
@Table(name = "traffic_signals")
public class TrafficSignal {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "intersection_id", nullable = false)
    private Intersection intersection;

    @Column(nullable = false, unique = true, length = 48)
    private String code;

    @Column(nullable = false, length = 200)
    private String name;

    private String description;

    @Column(length = 200)
    private String approach;

    @Enumerated(EnumType.STRING)
    @Column(name = "configuration_source", nullable = false, length = 32)
    private ConfigurationSource configurationSource;

    protected TrafficSignal() {
        // for JPA
    }

    TrafficSignal(Intersection intersection, String code, String name, ConfigurationSource configurationSource) {
        this.intersection = intersection;
        this.code = code;
        this.name = name;
        this.configurationSource = configurationSource;
    }

    public Long getId() {
        return id;
    }

    public Intersection getIntersection() {
        return intersection;
    }

    public String getCode() {
        return code;
    }

    public String getName() {
        return name;
    }

    public String getDescription() {
        return description;
    }

    public String getApproach() {
        return approach;
    }

    public void setApproach(String approach) {
        this.approach = approach;
    }

    public ConfigurationSource getConfigurationSource() {
        return configurationSource;
    }

    public boolean belongsTo(Long intersectionId) {
        return intersection.getId().equals(intersectionId);
    }
}
