--1
INSERT INTO "USER_ACCOUNT" (
    "user_id", "username", "PASSWORD"
) 
VALUES (
    '64302ea1-212d-414c-a2db-1fad0b3c3b6e','nisyyah','Nisyyah@123'
    ),
    ('3b9c1e2a-5d4f-4c8e-9a1b-2f3d4e5f6a7b','bluey','Bluey@123'
    ),
    ('4c8e9a1b-2f3d-4e5f-8a7b-8c9d0e1f2a3b','mabel','Mabel@123'
    ),
    ('6a7b9a1b-2f3d-4e5f-9a7b-8c9d0e1f2a3d','harry','Harry@123'
    ),
    ('7b8c9a1b-2f3d-4e5f-1a7b-8c9d0e1f2a3e','hermione','Hermione@123'
    ),
    ('8c9d0e1f-2a3b-4c5d-2e7f-8a9b0c1d2e3f','ron','Ron@123'
    ),
    ('9d0e1f2a-3b4c-5d6e-3f8a-9b0c1d2e3f4a','luna','Luna@123'
    ),
    ('0e1f2a3b-4c5d-6e7f-4a9b-0c1d2e3f4a5b','snape','Snape@123'
    ),
    ('1f2a3b4c-5d6e-7f8a-5b0c-1d2e3f4a5b6c','voldemort','Voldemort@123'
    ),
    ('2a3b4c5d-6e7f-8a9b-6c1d-2e3f4a5b6c7d','sirius','Sirius@123'
    ),
    ('3b4c5d6e-7f8a-9b0c-7d2e-3f4a5b6c7d8e','remus','Remus@123'
    ),
    ('4c5d6e7f-8a9b-0c1d-8e3f-4a5b6c7d8e9f','fred','Fred@123'
    );

--2
INSERT INTO "ROLE" (
    "role_id", "role_name"
) VALUES (
    'ad98db8d-2f94-4176-9f47-7c5ed55cdeb4', 'administrator'
    ),
    ('bd98db8d-2f94-4176-9f47-7c5ed55cdeb4', 'organizer'
    ),
    ('cd98db8d-2f94-4176-9f47-7c5ed55cdeb4', 'customer'
    );
    
--3
INSERT INTO "ACCOUNT_ROLE" (
    "role_id", "user_id"
) VALUES (
    'ad98db8d-2f94-4176-9f47-7c5ed55cdeb4', '64302ea1-212d-414c-a2db-1fad0b3c3b6e'
    ),
    ('bd98db8d-2f94-4176-9f47-7c5ed55cdeb4', '3b9c1e2a-5d4f-4c8e-9a1b-2f3d4e5f6a7b'
    ),
    ('cd98db8d-2f94-4176-9f47-7c5ed55cdeb4', '4c8e9a1b-2f3d-4e5f-8a7b-8c9d0e1f2a3b'
    ),
    ('cd98db8d-2f94-4176-9f47-7c5ed55cdeb4', '6a7b9a1b-2f3d-4e5f-9a7b-8c9d0e1f2a3d'
    ),
    ('cd98db8d-2f94-4176-9f47-7c5ed55cdeb4', '7b8c9a1b-2f3d-4e5f-1a7b-8c9d0e1f2a3e'
    ),
    ('cd98db8d-2f94-4176-9f47-7c5ed55cdeb4', '8c9d0e1f-2a3b-4c5d-2e7f-8a9b0c1d2e3f'
    ),
    ('cd98db8d-2f94-4176-9f47-7c5ed55cdeb4', '9d0e1f2a-3b4c-5d6e-3f8a-9b0c1d2e3f4a'
    ),
    ('cd98db8d-2f94-4176-9f47-7c5ed55cdeb4', '0e1f2a3b-4c5d-6e7f-4a9b-0c1d2e3f4a5b'
    ),
    ('cd98db8d-2f94-4176-9f47-7c5ed55cdeb4', '1f2a3b4c-5d6e-7f8a-5b0c-1d2e3f4a5b6c'
    ),
    ('cd98db8d-2f94-4176-9f47-7c5ed55cdeb4', '2a3b4c5d-6e7f-8a9b-6c1d-2e3f4a5b6c7d'
    ),
    ('cd98db8d-2f94-4176-9f47-7c5ed55cdeb4', '3b4c5d6e-7f8a-9b0c-7d2e-3f4a5b6c7d8e'
    ),
    ('cd98db8d-2f94-4176-9f47-7c5ed55cdeb4', '4c5d6e7f-8a9b-0c1d-8e3f-4a5b6c7d8e9f'
    ),
    ('cd98db8d-2f94-4176-9f47-7c5ed55cdeb4', '6a7b9a1b-2f3d-4e5f-9a7b-8c9d0e1f2a3d'
    ),
    ('cd98db8d-2f94-4176-9f47-7c5ed55cdeb4', '7b8c9a1b-2f3d-4e5f-1a7b-8c9d0e1f2a3e'
    ),
    ('cd98db8d-2f94-4176-9f47-7c5ed55cdeb4', '8c9d0e1f-2a3b-4c5d-2e7f-8a9b0c1d2e3f'
    );

--4
INSERT INTO "ARTIST" (
    "artist_id", "name", "genre"
) 
VALUES  ('a1b2c3d4-0001-4000-a000-000000000001', 'SEVENTEEN', 'K-Pop'),
        ('a1b2c3d4-0002-4000-a000-000000000002', 'Harry Styles', 'Pop'),
        ('a1b2c3d4-0003-4000-a000-000000000003', 'The Rose', 'Indie Rock'),
        ('a1b2c3d4-0004-4000-a000-000000000004', 'Adele', 'Soul'),
        ('a1b2c3d4-0005-4000-a000-000000000005', 'Coldplay', 'Alternative Rock'),
        ('a1b2c3d4-0006-4000-a000-000000000006', 'Taylor Swift', 'Pop'),
        ('a1b2c3d4-0007-4000-a000-000000000007', 'Bruno Mars', 'Funk Pop'),
        ('a1b2c3d4-0008-4000-a000-000000000008', 'Billie Eilish', 'Alternative Pop');

--5 # Note: Ensure that the referenced event_id values exist in the "EVENT" table before running this insert statement.
INSERT INTO "TICKET_CATEGORY" (
    "category_id", "category_name", "quota", "price", "tevent_id"
)
VALUES  ('c1d2e3f4-0001-4000-a000-000000000001', 'VIP', 100, 500.00, 'e1f2g3h4-0001-4000-a000-000000000001'),
        ('c1d2e3f4-0002-4000-a000-000000000002', 'Regular', 500, 150.00, 'e1f2g3h4-0001-4000-a000-000000000001'),
        ('c1d2e3f4-0003-4000-a000-000000000003', 'Balcony', 200, 300.00, 'e1f2g3h4-0002-4000-a000-000000000002'),
        ('c1d2e3f4-0004-4000-a000-000000000004', 'Regular', 1000, 50.00, 'e1f2g3h4-0003-4000-a000-000000000003'),
        ('c1d2e3f4-0005-4000-a000-000000000005', 'Early Bird', 150, 100.00, 'e1f2g3h4-0004-4000-a000-000000000004'),
        ('c1d2e3f4-0006-4000-a000-000000000006', 'Premium', 50, 800.00, 'e1f2g3h4-0005-4000-a000-000000000005'),
        ('c1d2e3f4-0007-4000-a000-000000000007', 'Regular', 300, 200.00, 'e1f2g3h4-0006-4000-a000-000000000006'),
        ('c1d2e3f4-0008-4000-a000-000000000008', 'Student', 200, 75.00, 'e1f2g3h4-0007-4000-a000-000000000007'),
        ('c1d2e3f4-0009-4000-a000-000000000009', 'Family Pack', 100, 250.00, 'e1f2g3h4-0008-4000-a000-000000000008'),
        ('c1d2e3f4-0010-4000-a000-000000000010', 'Group Discount', 200, 180.00, 'e1f2g3h4-0009-4000-a000-000000000009'),
        ('c1d2e3f4-0011-4000-a000-000000000011', 'Last Minute', 50, 120.00, 'e1f2g3h4-0010-4000-a000-000000000010'),
        ('c1d2e3f4-0012-4000-a000-000000000012', 'VIP', 20, 1000.00, 'e1f2g3h4-0011-4000-a000-000000000011'),
        ('c1d2e3f4-0014-4000-a000-000000000014', 'Balcony', 10, 1500.00, 'e1f2g3h4-0013-4000-a000-000000000013'),
        ('c1d2e3f4-0015-4000-a000-000000000015', 'Regular', 500, 100.00, 'e1f2g3h4-0014-4000-a000-000000000014');

--6
INSERT INTO "VENUE" (
    "venue_id", "venue_name", "capacity", "address", "city"
) VALUES  ('f1e2d3c4-0001-4000-a000-000000000001', 'Stadium A', 50000, '123 Main St', 'Cityville'),
        ('f1e2d3c4-0002-4000-a000-000000000002', 'Arena B', 20000, '456 Elm St', 'Townsburg'),
        ('f1e2d3c4-0003-4000-a000-000000000003', 'Theater C', 5000, '789 Oak St', 'Villageton'),
        ('f1e2d3c4-0004-4000-a000-000000000004', 'Concert Hall D', 3000, '321 Pine St', 'Metropolis'),
        ('f1e2d3c4-0005-4000-a000-000000000005', 'Open Air Venue E', 10000, '654 Maple St', 'Lakeside'),
        ('f1e2d3c4-0006-4000-a000-000000000006', 'Club F', 800, '987 Cedar St', 'Downtown'),
        ('f1e2d3c4-0007-4000-a000-000000000007', 'Festival Grounds G', 15000, '246 Birch St', 'Countryside');
--7
INSERT INTO "EVENT" (
    "event_id", "event_datetime", "event_title", "venue_id", "organizer_id"
) VALUES  ('e1f2g3h4-0001-4000-a000-000000000001', '2024-12-01 20:00:00', 'SEVENTEEN World Tour', 'v1e2n3u4-0001-4000-a000-000000000001', '3b9c1e2a-5d4f-4c8e-9a1b-2f3d4e5f6a7b'),
        ('e1f2g3h4-0002-4000-a000-000000000002', 'Harry Styles Live in Concert', 'v1e2n3u4-0002-4000-a000-000000000002', '3b9c1e2a-5d4f-4c8e-9a1b-2f3d4e5f6a7b'),
        ('e1f2g3h4-0003-4000-a000-000000000003', 'The Rose Acoustic Night', 'v1e2n3u4-0003-4000-a000-000000000003', '3b9c1e2a-5d4f-4c8e-9a1b-2f3d4e5f6a7b'),
        ('e1f2g3h4-0004-4000-a000-000000000004', 'Adele Live at Sydney Opera House', 'v1e2n3u4-0004-4000-a000-000000000004', '3b9c1e2a-5d4f-4c8e-9a1b-2f3d4e5f6a7b'),
        ('e1f2g3h4-0005-4000-a000-000000000005', 'Coldplay Music of the Spheres Tour', 'v1e2n3u4-0005-4000-a000-000000000005', '3b9c1e2a-5d4f-4c8e-9a1b-2f3d4e5f6a7b'),
        ('e1f2g3h4-0006-4000-a000-000000000006', 'Taylor Swift Eras Tour', 'v1e2n3u4-0006-4000-a000-000000000006', '3b9c1e2a-5d4f-4c8e-9a1b-2f3d4e5f6a7b'),
        ('e1f2g3h4-0007-4000-a000-000000000007', 'Bruno Mars 24K Magic World Tour', 'v1e2n3u4-0007-4000-a000-000000000007', '3b9c1e2a-5d4f-4c8e-9a1b-2f3d4e5f6a7b');

--8
INSERT INTO "ORGANIZER" (
    "organizer_id", "organizer_name", "contact_email", "user_id"
) VALUES  ('3b9c1e2a-5d4f-4c8e-9a1b-2f3d4e5f6a7b', 'Global Events Inc.', 'contact@globalevents.com', '64302ea1-212d-414c-a2db-1fad0b3c3b6e'),
        ('4c8e9a1b-2f3d-4e5f-8a7b-8c9d0e1f2a3b', 'City Concerts Ltd.', 'contact@cityconcerts.com', '75413fb2-323e-425d-b3ec-2gb1c4d5e6f7'),
        ('6a7b9a1b-2f3d-4e5f-9a7b-8c9d0e1f2a3d', 'Music Mania Co.', 'contact@musicmania.com', '86524gc3-434f-436e-0b2c-3hc2d5e6f7g8'),
        ('7b8c9a1b-2f3d-4e5f-1a7b-8c9d0e1f2a3e', 'Star Events Group', 'contact@starevents.com', '97635hd4-545g-547f-1c3d-4id3e6f7g8h9');