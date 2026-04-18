DROP TABLE IF EXISTS "USER_ACCOUNT" CASCADE;
DROP TABLE IF EXISTS "ROLE" CASCADE;
DROP TABLE IF EXISTS "ACCOUNT_ROLE" CASCADE;
DROP TABLE IF EXISTS "CUSTOMER" CASCADE;
DROP TABLE IF EXISTS "ORGANIZER" CASCADE;
DROP TABLE IF EXISTS "VENUE" CASCADE;
DROP TABLE IF EXISTS "SEAT" CASCADE;
DROP TABLE IF EXISTS "EVENT" CASCADE;
DROP TABLE IF EXISTS "ARTIST" CASCADE;
DROP TABLE IF EXISTS "EVENT_ARTIST" CASCADE;
DROP TABLE IF EXISTS "TICKET_CATEGORY" CASCADE;
DROP TABLE IF EXISTS "TICKET" CASCADE;
DROP TABLE IF EXISTS "HAS_RELATIONSHIP" CASCADE;
DROP TABLE IF EXISTS "ORDER" CASCADE;
DROP TABLE IF EXISTS "PROMOTION" CASCADE;
DROP TABLE IF EXISTS "ORDER_PROMOTION" CASCADE;

-- 1
CREATE TABLE "USER_ACCOUNT" (
  "user_id" UUID DEFAULT GEN_RANDOM_UUID(), 
  "username" VARCHAR(100) UNIQUE NOT NULL, 
  "PASSWORD" VARCHAR(255) NOT NULL CHECK (
    LENGTH("PASSWORD") >= 8 AND 
    "PASSWORD" ~ '[A-Z]' AND 
    "PASSWORD" ~ '[a-z]' AND 
    "PASSWORD" ~ '[0-9]' AND 
    "PASSWORD" ~ '[!@#$%^&*(),.?":{}|<>]'
  ), 
  PRIMARY KEY ("user_id")
);

-- 2
CREATE TABLE "ROLE" (
  "role_id" UUID UNIQUE, 
  "role_name" VARCHAR (50) UNIQUE NOT NULL, 
    PRIMARY KEY ("role_id")
);

-- 3
CREATE TABLE "ACCOUNT_ROLE" (
  "role_id" UUID , 
  "user_id" UUID , 
    PRIMARY KEY ("role_id", "user_id"),
    FOREIGN KEY ("user_id") REFERENCES "USER_ACCOUNT" ("user_id"),
    FOREIGN KEY ("role_id") REFERENCES "ROLE" ("role_id")
);

-- 4
CREATE TABLE "CUSTOMER" (
    "customer_id" UUID DEFAULT GEN_RANDOM_UUID(), 
    "full_name" VARCHAR(100) NOT NULL, 
    "phone_number" VARCHAR(20) , 
    "user_id" UUID UNIQUE NOT NULL,
    PRIMARY KEY ("customer_id"),
    FOREIGN KEY ("user_id") REFERENCES "USER_ACCOUNT" ("user_id")
);

-- 5
CREATE TABLE "ORGANIZER" (
    "organizer_id" UUID DEFAULT GEN_RANDOM_UUID(), 
    "organization_name" VARCHAR(100) NOT NULL, 
    "contact_email" VARCHAR(100) , 
    "user_id" UUID UNIQUE NOT NULL,
    PRIMARY KEY ("organizer_id"),
    FOREIGN KEY ("user_id") REFERENCES "USER_ACCOUNT" ("user_id")
);

-- 6
CREATE TABLE "VENUE" (
    "venue_id" UUID DEFAULT GEN_RANDOM_UUID(), 
    "venue_name" VARCHAR(100) NOT NULL, 
    "capacity" INTEGER NOT NULL CHECK ("capacity" > 0),
    "address" TEXT NOT NULL, 
    "city" VARCHAR(100) NOT NULL,
    PRIMARY KEY ("venue_id")
);

-- 7
CREATE TABLE "SEAT" (
    "seat_id" UUID DEFAULT GEN_RANDOM_UUID(), 
    "section" VARCHAR(50) NOT NULL,
    "seat_number" VARCHAR(10) NOT NULL, 
    "row_number" VARCHAR(10) NOT NULL,
    "venue_id" UUID NOT NULL,
    PRIMARY KEY ("seat_id"),
    FOREIGN KEY ("venue_id") REFERENCES "VENUE" ("venue_id")
);

-- 8
CREATE TABLE "EVENT" (
    "event_id" UUID DEFAULT GEN_RANDOM_UUID(), 
    "event_datetime" TIMESTAMP NOT NULL,
    "event_title" VARCHAR(200) NOT NULL,
    "venue_id" UUID NOT NULL,
    "organizer_id" UUID NOT NULL,
    PRIMARY KEY ("event_id"),
    FOREIGN KEY ("organizer_id") REFERENCES "ORGANIZER" ("organizer_id"),
    FOREIGN KEY ("venue_id") REFERENCES "VENUE" ("venue_id")
);

-- 9
CREATE TABLE "ARTIST" (
    "artist_id" UUID DEFAULT GEN_RANDOM_UUID(), 
    "name" VARCHAR(100) NOT NULL, 
    "genre" VARCHAR(100),
    PRIMARY KEY ("artist_id")
);

-- 10
CREATE TABLE "EVENT_ARTIST" (
    "event_id" UUID ,
    "artist_id" UUID ,
    "role" VARCHAR(100) ,
    PRIMARY KEY ("event_id", "artist_id"),
    FOREIGN KEY ("event_id") REFERENCES "EVENT" ("event_id"),
    FOREIGN KEY ("artist_id") REFERENCES "ARTIST" ("artist_id")
);

-- 11
CREATE TABLE "TICKET_CATEGORY" (
    "category_id" UUID DEFAULT GEN_RANDOM_UUID(), 
    "category_name" VARCHAR(50) NOT NULL, 
    "quota" INTEGER NOT NULL CHECK ("quota" > 0),
    "price" NUMERIC(12, 2) NOT NULL CHECK ("price" >= 0),
    "tevent_id" UUID NOT NULL,
    PRIMARY KEY ("category_id"),
    FOREIGN KEY ("tevent_id") REFERENCES "EVENT" ("event_id")
);

-- 12
CREATE TABLE "TICKET" (
    "ticket_id" UUID DEFAULT GEN_RANDOM_UUID(), 
    "ticket_code" VARCHAR(100) UNIQUE NOT NULL,
    "tcategory_id" UUID NOT NULL,
    "torder_id" UUID NOT NULL,
    PRIMARY KEY ("ticket_id"),
    FOREIGN KEY ("tcategory_id") REFERENCES "TICKET_CATEGORY" ("category_id"),
    FOREIGN KEY ("torder_id") REFERENCES "ORDER" ("order_id")
);

-- 13
CREATE TABLE "HAS_RELATIONSHIP" (
    "seat_id" UUID ,
    "ticket_id" UUID ,
    PRIMARY KEY ("seat_id", "ticket_id"),
    FOREIGN KEY ("seat_id") REFERENCES "SEAT" ("seat_id"),
    FOREIGN KEY ("ticket_id") REFERENCES "TICKET" ("ticket_id")
);

-- 14
CREATE TABLE "ORDER" (
    "order_id" UUID DEFAULT GEN_RANDOM_UUID(), 
    "order_date" TIMESTAMP NOT NULL,
    "payment_status" VARCHAR(20) NOT NULL CHECK ("payment_status" IN ('Pending', 'Completed', 'Failed')),
    "total_amount" NUMERIC(12, 2) NOT NULL CHECK ("total_amount" >= 0),
    "customer_id" UUID NOT NULL,
    PRIMARY KEY ("order_id"),
    FOREIGN KEY ("customer_id") REFERENCES "CUSTOMER" ("customer_id")
);

-- 15
CREATE TABLE "PROMOTION" (
    "promotion_id" UUID DEFAULT GEN_RANDOM_UUID(), 
    "promo_code" VARCHAR(50) UNIQUE NOT NULL,
    "discount_type" VARCHAR(20) NOT NULL CHECK ("discount_type" IN ('NOMINAL', 'PERCENTAGE')),
    "discount_value" NUMERIC(12, 2) NOT NULL CHECK ("discount_value" >= 0),
    "start_date" DATE NOT NULL,
    "end_date" DATE NOT NULL,
    "use_limit" INTEGER NOT NULL CHECK ("use_limit" > 0),
    PRIMARY KEY ("promotion_id")
);

-- 16
CREATE TABLE "ORDER_PROMOTION" (
    "order_promotion_id" UUID DEFAULT GEN_RANDOM_UUID(),
    "promotion_id" UUID NOT NULL,
    "order_id" UUID NOT NULL,
    PRIMARY KEY ("order_promotion_id"),
    FOREIGN KEY ("order_id") REFERENCES "ORDER" ("order_id"),
    FOREIGN KEY ("promotion_id") REFERENCES "PROMOTION" ("promotion_id")
);