-- STORED PROCEDURE REGISTER CUSTOMER
CREATE OR REPLACE PROCEDURE register_customer(
    p_full_name VARCHAR,
    p_phone_number VARCHAR,
    p_username VARCHAR,
    p_password VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_user_id UUID;
BEGIN
    INSERT INTO "USER_ACCOUNT" ("username", "PASSWORD")
    VALUES (p_username, p_password)
    RETURNING "user_id" INTO v_user_id;

    INSERT INTO "CUSTOMER" ("full_name", "phone_number", "user_id")
    VALUES (p_full_name, p_phone_number, v_user_id);
END;
$$;

-- TRIGGER FUNCTION VALIDASI USERNAME
CREATE OR REPLACE FUNCTION validate_username()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- VALIDASI KARAKTER SPESIAL
    IF NEW."username" !~ '^[a-zA-Z0-9]+$' THEN
        RAISE EXCEPTION
        'ERROR: Username "%" hanya boleh mengandung huruf dan angka tanpa simbol atau spasi.',
        NEW."username";
    END IF;
    -- VALIDASI DUPLIKAT CASE-INSENSITIVE
    IF EXISTS (
        SELECT 1
        FROM "USER_ACCOUNT"
        WHERE LOWER("username") = LOWER(NEW."username")
    ) THEN
        RAISE EXCEPTION
        'ERROR: Username "%" sudah terdaftar, gunakan username lain.',
        NEW."username";
    END IF;
    RETURN NEW;
END;
$$;

-- TRIGGER USERNAME
DROP TRIGGER IF EXISTS trg_validate_username ON "USER_ACCOUNT";
CREATE TRIGGER trg_validate_username
BEFORE INSERT ON "USER_ACCOUNT"
FOR EACH ROW
EXECUTE FUNCTION validate_username();