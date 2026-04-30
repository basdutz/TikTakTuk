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
    ('bd98db8d-2f94-4176-9f47-7c5ed55cdeb4', '4c8e9a1b-2f3d-4e5f-8a7b-8c9d0e1f2a3b'
    ),
    ('bd98db8d-2f94-4176-9f47-7c5ed55cdeb4', '6a7b9a1b-2f3d-4e5f-9a7b-8c9d0e1f2a3d'
    ),
    ('bd98db8d-2f94-4176-9f47-7c5ed55cdeb4', '7b8c9a1b-2f3d-4e5f-1a7b-8c9d0e1f2a3e'
    ),
    ('bd98db8d-2f94-4176-9f47-7c5ed55cdeb4', '8c9d0e1f-2a3b-4c5d-2e7f-8a9b0c1d2e3f'
    ),
    ('bd98db8d-2f94-4176-9f47-7c5ed55cdeb4', '9d0e1f2a-3b4c-5d6e-3f8a-9b0c1d2e3f4a'
    ),
    ('bd98db8d-2f94-4176-9f47-7c5ed55cdeb4', '0e1f2a3b-4c5d-6e7f-4a9b-0c1d2e3f4a5b'
    ),
    ('bd98db8d-2f94-4176-9f47-7c5ed55cdeb4', '1f2a3b4c-5d6e-7f8a-5b0c-1d2e3f4a5b6c'
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
    );

-- CUSTOMER
INSERT INTO "CUSTOMER" (
    "customer_id", "full_name", "phone_number", "user_id"
) VALUES
    ('c0000001-0000-4000-a000-000000000001', 'Mabel Pines',      '081234567001', '4c8e9a1b-2f3d-4e5f-8a7b-8c9d0e1f2a3b'),
    ('c0000001-0000-4000-a000-000000000002', 'Harry Potter',     '081234567002', '6a7b9a1b-2f3d-4e5f-9a7b-8c9d0e1f2a3d'),
    ('c0000001-0000-4000-a000-000000000003', 'Hermione Granger', '081234567003', '7b8c9a1b-2f3d-4e5f-1a7b-8c9d0e1f2a3e'),
    ('c0000001-0000-4000-a000-000000000004', 'Ron Weasley',      '081234567004', '8c9d0e1f-2a3b-4c5d-2e7f-8a9b0c1d2e3f'),
    ('c0000001-0000-4000-a000-000000000005', 'Luna Lovegood',    '081234567005', '9d0e1f2a-3b4c-5d6e-3f8a-9b0c1d2e3f4a'),
    ('c0000001-0000-4000-a000-000000000006', 'Severus Snape',    '081234567006', '0e1f2a3b-4c5d-6e7f-4a9b-0c1d2e3f4a5b'),
    ('c0000001-0000-4000-a000-000000000007', 'Lord Voldemort',   '081234567007', '1f2a3b4c-5d6e-7f8a-5b0c-1d2e3f4a5b6c'),
    ('c0000001-0000-4000-a000-000000000008', 'Sirius Black',     '081234567008', '2a3b4c5d-6e7f-8a9b-6c1d-2e3f4a5b6c7d'),
    ('c0000001-0000-4000-a000-000000000009', 'Remus Lupin',      '081234567009', '3b4c5d6e-7f8a-9b0c-7d2e-3f4a5b6c7d8e'),
    ('c0000001-0000-4000-a000-000000000010', 'Fred Weasley',     '081234567010', '4c5d6e7f-8a9b-0c1d-8e3f-4a5b6c7d8e9f');


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

--5
INSERT INTO "ORGANIZER" (
    "organizer_id", "organization_name", "contact_email", "user_id"
) VALUES  ('550e8400-e29b-41d4-a716-446655440000', 'EventCo', 'contact@eventco.com', '4c8e9a1b-2f3d-4e5f-8a7b-8c9d0e1f2a3b'),
        ('550e8400-e29b-41d4-a716-446655440001', 'MusicFest Inc.', 'contact@musicfest.com', '3b9c1e2a-5d4f-4c8e-9a1b-2f3d4e5f6a7b'),
        ('550e8400-e29b-41d4-a716-446655440002', 'LiveNation', 'contact@livenation.com', '6a7b9a1b-2f3d-4e5f-9a7b-8c9d0e1f2a3d'),
        ('550e8400-e29b-41d4-a716-446655440003', 'ConcertsRUs', 'contact@concertsrus.com', '7b8c9a1b-2f3d-4e5f-1a7b-8c9d0e1f2a3e');

--6
INSERT INTO "VENUE" (
    "venue_id", "venue_name", "capacity", "address", "city"
) VALUES ('f1e2d3c4-0001-4000-a000-000000000001','Stadium A',50000,'123 Main St','Cityville'),
    ('f1e2d3c4-0002-4000-a000-000000000002','Arena B',20000,'456 Elm St','Townsburg'),
    ('f1e2d3c4-0003-4000-a000-000000000003','Theater C',5000,'789 Oak St','Villageton'),
    ('f1e2d3c4-0004-4000-a000-000000000004','Concert Hall D',3000,'321 Pine St','Metropolis'),
    ('f1e2d3c4-0005-4000-a000-000000000005','Open Air Venue E',10000,'654 Maple St','Lakeside'),
    ('f1e2d3c4-0006-4000-a000-000000000006','Club F',800,'987 Cedar St','Downtown'),
    ('f1e2d3c4-0007-4000-a000-000000000007','Festival Grounds G',15000,'246 Birch St','Countryside');

--7
INSERT INTO "EVENT" (
    "event_id", "event_datetime", "event_title", "venue_id", "organizer_id"
) VALUES  ('e1f2a3b4-0001-4000-a000-000000000001','2024-12-01 19:00:00','SEVENTEEN World Tour','f1e2d3c4-0001-4000-a000-000000000001','550e8400-e29b-41d4-a716-446655440000'),
        ('e1f2a3b4-0002-4000-a000-000000000002','2024-11-15 20:00:00','Harry Styles Live','f1e2d3c4-0002-4000-a000-000000000002','550e8400-e29b-41d4-a716-446655440000'),
        ('e1f2a3b4-0003-4000-a000-000000000003','2024-10-20 18:30:00','The Rose Concert','f1e2d3c4-0003-4000-a000-000000000003','550e8400-e29b-41d4-a716-446655440000'),
        ('e1f2a3b4-0004-4000-a000-000000000004','2024-09-05 19:30:00','Adele Live','f1e2d3c4-0004-4000-a000-000000000004','550e8400-e29b-41d4-a716-446655440001'),
        ('e1f2a3b4-0005-4000-a000-000000000005','2024-08-10 20:00:00','Coldplay Festival','f1e2d3c4-0005-4000-a000-000000000005','550e8400-e29b-41d4-a716-446655440002'),
        ('e1f2a3b4-0006-4000-a000-000000000006','2024-07-25 19:00:00','Taylor Swift Tour','f1e2d3c4-0006-4000-a000-000000000006','550e8400-e29b-41d4-a716-446655440002'),
        ('e1f2a3b4-0007-4000-a000-000000000007','2024-06-30 20:30:00','Bruno Mars Tour','f1e2d3c4-0007-4000-a000-000000000007','550e8400-e29b-41d4-a716-446655440003'),
        ('e1f2a3b4-0008-4000-a000-000000000008','2024-05-15 18:00:00','Billie Eilish Tour','f1e2d3c4-0001-4000-a000-000000000001','550e8400-e29b-41d4-a716-446655440003');

--8
INSERT INTO "TICKET_CATEGORY" (
    "category_id", "category_name", "quota", "price", "tevent_id"
) VALUES
('c1d2e3f4-0001-4000-a000-000000000001', 'VIP', 100, 4000000, 'e1f2a3b4-0001-4000-a000-000000000001'),
('c1d2e3f4-0002-4000-a000-000000000002', 'Regular', 500, 2500000, 'e1f2a3b4-0001-4000-a000-000000000001'),
('c1d2e3f4-0003-4000-a000-000000000003', 'Balcony', 200, 3000000, 'e1f2a3b4-0002-4000-a000-000000000002'),
('c1d2e3f4-0004-4000-a000-000000000004', 'Regular', 1000, 1500000, 'e1f2a3b4-0003-4000-a000-000000000003'),
('c1d2e3f4-0005-4000-a000-000000000005', 'Early Bird', 150, 750000, 'e1f2a3b4-0004-4000-a000-000000000004'),
('c1d2e3f4-0006-4000-a000-000000000006', 'Premium', 50, 4000000, 'e1f2a3b4-0005-4000-a000-000000000005'),
('c1d2e3f4-0007-4000-a000-000000000007', 'Regular', 300, 1200000, 'e1f2a3b4-0006-4000-a000-000000000006'),
('c1d2e3f4-0008-4000-a000-000000000008', 'Student', 200, 750000, 'e1f2a3b4-0007-4000-a000-000000000007'),
('c1d2e3f4-0009-4000-a000-000000000009', 'Family Pack', 100, 8000000, 'e1f2a3b4-0008-4000-a000-000000000008'),
('c1d2e3f4-0010-4000-a000-000000000010', 'Group Discount', 200, 7500000, 'e1f2a3b4-0001-4000-a000-000000000001'),
('c1d2e3f4-0011-4000-a000-000000000011', 'Last Minute', 50, 2200000, 'e1f2a3b4-0002-4000-a000-000000000002'),
('c1d2e3f4-0012-4000-a000-000000000012', 'VIP', 20, 3500000, 'e1f2a3b4-0003-4000-a000-000000000003'),
('c1d2e3f4-0013-4000-a000-000000000013', 'Premium', 30, 4500000, 'e1f2a3b4-0004-4000-a000-000000000004'),
('c1d2e3f4-0014-4000-a000-000000000014', 'Balcony', 10, 3000000, 'e1f2a3b4-0005-4000-a000-000000000005'),
('c1d2e3f4-0015-4000-a000-000000000015', 'Regular', 500, 1000000, 'e1f2a3b4-0006-4000-a000-000000000006');