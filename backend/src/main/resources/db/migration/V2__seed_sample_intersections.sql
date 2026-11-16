-- Demonstration intersections in Łódź.
--
-- * Coordinates and OSM node ids come from OpenStreetMap (© OpenStreetMap contributors, ODbL),
--   via research/osm/export_seed_intersections.py. The coordinate is the centroid of the road
--   nodes clustered as one intersection by research/osm/build_intersections_v2.py.
-- * Traffic SIGNAL GROUPS below are SAMPLE configurations invented for the demo. OpenStreetMap
--   does not record which approaches a signal controls or its timing, and these have not been
--   verified on site. They must not be read as real signal configurations.

INSERT INTO intersections (code, name, city, description, latitude, longitude, location_source, osm_reference)
VALUES
    ('LDZ-KOS-STR', 'Al. Kościuszki / Struga', 'Łódź',
     'Signalised intersection in the city centre. Location derived from OpenStreetMap; signal groups are sample data.',
     51.7652940, 19.4543812, 'OPENSTREETMAP', 'traffic_signals nodes: 1537900461, 9588437613, 9588437614'),
    ('LDZ-KOS-ZAM', 'Al. Kościuszki / Zamenhofa', 'Łódź',
     'Signalised intersection in the city centre. Location derived from OpenStreetMap; signal groups are sample data.',
     51.7621214, 19.4551228, 'OPENSTREETMAP', 'traffic_signals nodes: 9588469418, 9588469419, 9588469420'),
    ('LDZ-SIE-NAR', 'Sienkiewicza / Narutowicza', 'Łódź',
     'Signalised intersection east of Piotrkowska Street. Location derived from OpenStreetMap; signal groups are sample data.',
     51.7709159, 19.4604567, 'OPENSTREETMAP', 'traffic_signals nodes: 1745409253, 3332843788, 5241067534'),
    ('LDZ-KOP-POM', 'Kopcińskiego / Pomorska (Rondo Solidarności)', 'Łódź',
     'Large junction at Rondo Solidarności. Location derived from OpenStreetMap; signal groups are sample data.',
     51.7789976, 19.4815992, 'OPENSTREETMAP', 'traffic_signals nodes: 1643067025, 3100390638, 12708251633'),
    ('LDZ-PRZ-LEC', 'Przybyszewskiego / Łęczycka', 'Łódź',
     'Signalised intersection in Górna district. Location derived from OpenStreetMap; signal groups are sample data.',
     51.7470235, 19.4844344, 'OPENSTREETMAP',
     'traffic_signals nodes: 12559432014, 12559432015, 12559432018, 12559432019, 12559432020, 12559432021'),
    ('LDZ-BAR-PAB', 'Al. Bartoszewskiego / Pabianicka', 'Łódź',
     'Signalised intersection in the south of the city. Location derived from OpenStreetMap; signal groups are sample data.',
     51.7267223, 19.4478496, 'OPENSTREETMAP', 'traffic_signals nodes: 2974125268, 3334312372, 3721722731');

INSERT INTO traffic_signals (intersection_id, code, name, description, approach, configuration_source)
SELECT i.id, s.code, s.name, s.description, s.approach, 'SAMPLE'
FROM (VALUES
    ('LDZ-KOS-STR', 'LDZ-KOS-STR-S1', 'Main road signal group', 'Sample vehicle signal group for the main road.', 'Al. Tadeusza Kościuszki'),
    ('LDZ-KOS-STR', 'LDZ-KOS-STR-S2', 'Cross street signal group', 'Sample vehicle signal group for the cross street.', 'Andrzeja Struga'),
    ('LDZ-KOS-ZAM', 'LDZ-KOS-ZAM-S1', 'Main road signal group', 'Sample vehicle signal group for the main road.', 'Al. Tadeusza Kościuszki'),
    ('LDZ-KOS-ZAM', 'LDZ-KOS-ZAM-S2', 'Cross street signal group', 'Sample vehicle signal group for the cross street.', 'Ludwika Zamenhofa'),
    ('LDZ-SIE-NAR', 'LDZ-SIE-NAR-S1', 'Main road signal group', 'Sample vehicle signal group for the main road.', 'Henryka Sienkiewicza'),
    ('LDZ-SIE-NAR', 'LDZ-SIE-NAR-S2', 'Cross street signal group', 'Sample vehicle signal group for the cross street.', 'Prezydenta Gabriela Narutowicza'),
    ('LDZ-KOP-POM', 'LDZ-KOP-POM-S1', 'Main road signal group', 'Sample vehicle signal group for the main road.', 'Doktora Stefana Kopcińskiego'),
    ('LDZ-KOP-POM', 'LDZ-KOP-POM-S2', 'Cross street signal group', 'Sample vehicle signal group for the cross street.', 'Pomorska'),
    ('LDZ-PRZ-LEC', 'LDZ-PRZ-LEC-S1', 'Main road signal group', 'Sample vehicle signal group for the main road.', 'Stanisława Przybyszewskiego'),
    ('LDZ-PRZ-LEC', 'LDZ-PRZ-LEC-S2', 'Cross street signal group', 'Sample vehicle signal group for the cross street.', 'Łęczycka'),
    ('LDZ-BAR-PAB', 'LDZ-BAR-PAB-S1', 'Main road signal group', 'Sample vehicle signal group for the main road.', 'Pabianicka'),
    ('LDZ-BAR-PAB', 'LDZ-BAR-PAB-S2', 'Cross street signal group', 'Sample vehicle signal group for the cross street.', 'Al. Władysława Bartoszewskiego')
) AS s (intersection_code, code, name, description, approach)
JOIN intersections i ON i.code = s.intersection_code
ORDER BY s.code;
