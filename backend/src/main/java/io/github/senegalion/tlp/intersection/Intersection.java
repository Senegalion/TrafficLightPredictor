package io.github.senegalion.tlp.intersection;

import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.OneToMany;
import jakarta.persistence.OrderBy;
import jakarta.persistence.Table;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "intersections")
public class Intersection {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true, length = 32)
    private String code;

    @Column(nullable = false, length = 200)
    private String name;

    @Column(nullable = false, length = 100)
    private String city;

    private String description;

    @Column(nullable = false)
    private double latitude;

    @Column(nullable = false)
    private double longitude;

    @Enumerated(EnumType.STRING)
    @Column(name = "location_source", nullable = false, length = 32)
    private LocationSource locationSource;

    @Column(name = "osm_reference")
    private String osmReference;

    @Column(name = "created_at", nullable = false, insertable = false, updatable = false)
    private Instant createdAt;

    @OneToMany(mappedBy = "intersection", cascade = CascadeType.ALL, orphanRemoval = true)
    @OrderBy("code ASC")
    private List<TrafficSignal> signals = new ArrayList<>();

    protected Intersection() {
        // for JPA
    }

    public Intersection(String code, String name, String city, double latitude, double longitude,
                        LocationSource locationSource) {
        this.code = code;
        this.name = name;
        this.city = city;
        this.latitude = latitude;
        this.longitude = longitude;
        this.locationSource = locationSource;
    }

    public TrafficSignal addSignal(String code, String name, ConfigurationSource configurationSource) {
        TrafficSignal signal = new TrafficSignal(this, code, name, configurationSource);
        signals.add(signal);
        return signal;
    }

    public Long getId() {
        return id;
    }

    public String getCode() {
        return code;
    }

    public String getName() {
        return name;
    }

    public String getCity() {
        return city;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public double getLatitude() {
        return latitude;
    }

    public double getLongitude() {
        return longitude;
    }

    public LocationSource getLocationSource() {
        return locationSource;
    }

    public String getOsmReference() {
        return osmReference;
    }

    public List<TrafficSignal> getSignals() {
        return List.copyOf(signals);
    }
}
