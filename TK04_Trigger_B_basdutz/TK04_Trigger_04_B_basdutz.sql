-- STORED PROCEDURE: validate_promotion_on_order
-- Melakukan 2 validasi:
--   4.1 Cek promotion terdaftar & belum melebihi usage_limit
--   4.2 Cek tanggal event berada dalam periode promo

CREATE OR REPLACE FUNCTION validate_promotion_on_order()
RETURNS TRIGGER AS $$
DECLARE
    v_promotion         RECORD;
    v_usage_count       INTEGER;
    v_event_date        TIMESTAMP;
BEGIN
    -- VALIDASI 4.1a: Cek apakah promotion_id terdaftar
    SELECT *
    INTO v_promotion
    FROM PROMOTION
    WHERE promotion_id = NEW.promotion_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'ERROR: Promotion dengan ID % tidak ditemukan.', NEW.promotion_id;
    END IF;

    -- VALIDASI 4.1b: Cek apakah usage_limit belum terlampaui
    SELECT COUNT(*)
    INTO v_usage_count
    FROM ORDER_PROMOTION
    WHERE promotion_id = NEW.promotion_id;

    IF v_usage_count >= v_promotion.usage_limit THEN
        RAISE EXCEPTION 'ERROR: Promotion "%" telah mencapai batas maksimum penggunaan.', v_promotion.promo_code;
    END IF;

    -- VALIDASI 4.2: Cek tanggal event dalam periode promo
    -- Ambil event_date dari relasi ORDER -> TICKET -> TICKET_CATEGORY -> EVENT
    SELECT e.event_datetime
    INTO v_event_date
    FROM "ORDER" o
    JOIN TICKET t ON t.torder_id = o.order_id
    JOIN TICKET_CATEGORY tc ON tc.category_id = t.tcategory_id
    JOIN EVENT e ON e.event_id = tc.tevent_id
    WHERE o.order_id = NEW.order_id
    LIMIT 1;

    IF v_event_date IS NULL THEN
        RAISE EXCEPTION 'ERROR: Order dengan ID % tidak ditemukan atau belum memiliki tiket.', NEW.order_id;
    END IF;

    IF v_event_date::DATE < v_promotion.start_date OR v_event_date::DATE > v_promotion.end_date THEN
        RAISE EXCEPTION 'ERROR: Promotion "%" tidak berlaku untuk tanggal event ini.', v_promotion.promo_code;
    END IF;

    -- Semua validasi lolos, lanjutkan INSERT
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- TRIGGER: trigger_validate_promotion_on_order
-- Aktif BEFORE INSERT pada tabel ORDER_PROMOTION

DROP TRIGGER IF EXISTS trigger_validate_promotion_on_order ON ORDER_PROMOTION;

CREATE TRIGGER trigger_validate_promotion_on_order
BEFORE INSERT ON ORDER_PROMOTION
FOR EACH ROW
EXECUTE FUNCTION validate_promotion_on_order();
