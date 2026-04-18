--1
INSERT INTO "USER_ACCOUNT" (
    "user_id", "username", "password"
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
    