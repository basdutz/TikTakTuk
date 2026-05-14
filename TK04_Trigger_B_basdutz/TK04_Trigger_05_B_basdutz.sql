-- TRIGGER FUNCTION CEK KURSI SEBELUM DIHAPUS
CREATE OR REPLACE FUNCTION check_seat_before_delete()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM "HAS_RELATIONSHIP"
    WHERE "seat_id" = OLD."seat_id";

    IF v_count > 0 THEN
        RAISE EXCEPTION
        'ERROR: Kursi % - Baris % No. % tidak dapat dihapus karena sudah terisi.',
        OLD."section", OLD."row_number", OLD."seat_number";
    END IF;

    RETURN OLD;
END;
$$;

DROP TRIGGER IF EXISTS trg_check_seat_before_delete ON "SEAT";
CREATE TRIGGER trg_check_seat_before_delete
BEFORE DELETE ON "SEAT"
FOR EACH ROW
EXECUTE FUNCTION check_seat_before_delete();


-- TRIGGER FUNCTION CEK KUOTA SEBELUM BUAT TIKET
CREATE OR REPLACE FUNCTION check_ticket_quota()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_quota         INTEGER;
    v_sold          INTEGER;
    v_category_name VARCHAR;
BEGIN
    SELECT "quota", "category_name"
    INTO v_quota, v_category_name
    FROM "TICKET_CATEGORY"
    WHERE "category_id" = NEW."tcategory_id";

    SELECT COUNT(*) INTO v_sold
    FROM "TICKET"
    WHERE "tcategory_id" = NEW."tcategory_id";

    IF v_sold >= v_quota THEN
        RAISE EXCEPTION
        'ERROR: Kuota kategori tiket "%" sudah penuh. Tidak dapat membuat tiket baru.',
        v_category_name;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_check_ticket_quota ON "TICKET";
CREATE TRIGGER trg_check_ticket_quota
BEFORE INSERT ON "TICKET"
FOR EACH ROW
EXECUTE FUNCTION check_ticket_quota();