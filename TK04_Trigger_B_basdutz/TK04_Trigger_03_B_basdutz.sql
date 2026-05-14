-- TRIGGER FUNCTION EVENT_ARTIST VALIDATION
CREATE OR REPLACE FUNCTION validate_event_artist()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_artist_name VARCHAR;
    v_event_title VARCHAR;
BEGIN
    -- CEK ARTIST ADA
    IF NOT EXISTS (
        SELECT 1
        FROM "ARTIST"
        WHERE "artist_id" = NEW."artist_id"
    ) THEN
        RAISE EXCEPTION
        'ERROR: Artist dengan ID % tidak ditemukan.',
        NEW."artist_id";
    END IF;
    -- CEK EVENT ADA
    IF NOT EXISTS (
        SELECT 1
        FROM "EVENT"
        WHERE "event_id" = NEW."event_id"
    ) THEN
        RAISE EXCEPTION
        'ERROR: Event dengan ID % tidak ditemukan.',
        NEW."event_id";
    END IF;
    -- CEK DUPLIKAT EVENT_ARTIST
    IF EXISTS (
        SELECT 1
        FROM "EVENT_ARTIST"
        WHERE "artist_id" = NEW."artist_id"
        AND "event_id" = NEW."event_id"
    ) THEN
        SELECT "name"
        INTO v_artist_name
        FROM "ARTIST"
        WHERE "artist_id" = NEW."artist_id";

        SELECT "event_title"
        INTO v_event_title
        FROM "EVENT"
        WHERE "event_id" = NEW."event_id";

        RAISE EXCEPTION
        'ERROR: Artist "%" sudah terdaftar pada event "%".',
        v_artist_name,
        v_event_title;
    END IF;
    RETURN NEW;
END;
$$;

-- TRIGGER EVENT_ARTIST
DROP TRIGGER IF EXISTS trg_validate_event_artist ON "EVENT_ARTIST";
CREATE TRIGGER trg_validate_event_artist
BEFORE INSERT ON "EVENT_ARTIST"
FOR EACH ROW
EXECUTE FUNCTION validate_event_artist();

-- FUNCTION SISA KUOTA TIKET
CREATE OR REPLACE FUNCTION get_ticket_remaining_quota(
    p_event_id UUID
)
RETURNS TABLE (
    category_name VARCHAR,
    quota_awal INT,
    tiket_terjual BIGINT,
    sisa_kuota BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- VALIDASI EVENT
    IF NOT EXISTS (
        SELECT 1
        FROM "EVENT"
        WHERE "event_id" = p_event_id
    ) THEN
        RAISE EXCEPTION
        'ERROR: Event dengan ID % tidak ditemukan.',
        p_event_id;
    END IF;
    RETURN QUERY
    SELECT
        tc."category_name",
        tc."quota" AS quota_awal,
        COUNT(t."ticket_id") AS tiket_terjual,
        tc."quota" - COUNT(t."ticket_id") AS sisa_kuota
    FROM "TICKET_CATEGORY" tc
    LEFT JOIN "TICKET" t
        ON t."tcategory_id" = tc."category_id"
    WHERE tc."tevent_id" = p_event_id
    GROUP BY
        tc."category_name",
        tc."quota";
END;
$$;