-- Mencegah duplikasi nama Venue di kota yang sama (ignore case):
-- Saat Pengguna (Admin atau Organizer) ingin mendaftarkan Venue baru atau memperbarui nama Venue, sistem akan mengecek apakah sudah terdapat duplikasi (tanpa memperhatikan besar-kecilnya huruf) pada nama_venue di dalam kota yang sama. Jika ada duplikasi, sistem akan mencegah pendaftaran dan memberikan pesan error, yaitu:
-- "Venue <nama venue>'di kota '<nama kota>'sudah terdaftar dengan ID <id_venue>."
-- Contoh output error:
-- ERROR: Venue "Gelora Bung Karno" di kota "Jakarta" sudah terdaftar dengan ID d4ua-ed4e-41e2-bc8b-e7495.
CREATE OR REPLACE FUNCTION check_duplicate_venue()
RETURNS TRIGGER AS $$
DECLARE
    existing_id   UUID;
BEGIN
    -- Cek duplikasi nama venue (case-insensitive) di kota yang sama.
    -- Pada UPDATE, exclude row yang sedang di-update itu sendiri.
    SELECT v."venue_id"
    INTO existing_id
    FROM "VENUE" v
    WHERE LOWER(v."venue_name") = LOWER(NEW."venue_name")
      AND LOWER(v."city")       = LOWER(NEW."city")
      AND (TG_OP = 'INSERT' OR v."venue_id" <> NEW."venue_id")
    LIMIT 1;

    IF existing_id IS NOT NULL THEN
        RAISE EXCEPTION
        'Venue "%" di kota "%" sudah terdaftar dengan ID %.',
        NEW."venue_name",
        NEW."city",
        existing_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_check_duplicate_venue ON "VENUE";
CREATE TRIGGER trg_check_duplicate_venue
BEFORE INSERT OR UPDATE ON "VENUE"
FOR EACH ROW
EXECUTE FUNCTION check_duplicate_venue();

-- Mencegah penghapusan Venue jika masih memiliki Event aktif:
-- Saat Pengguna ingin menghapus salah satu Venue yang terdaftar, sistem akan mengecek apakah Venue tersebut memiliki Event yang masih dijadwalkan atau sedang berlangsung. Jika ada, sistem akan mencegah penghapusan dan memberikan pesan error, yaitu: "Venue <nama_venue>' masih memiliki event aktif sehingga tidak dapat dihapus."
-- Contoh output error:
-- ERROR: Venue "Istora Senayan" masih memiliki event aktif sehingga tidak dapat dihapus.
CREATE OR REPLACE FUNCTION prevent_venue_deletion()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM "EVENT" e
        WHERE e."venue_id" = OLD."venue_id"
          AND e."event_datetime" >= CURRENT_TIMESTAMP
    ) THEN
        RAISE EXCEPTION
        'Venue "%" masih memiliki event aktif sehingga tidak dapat dihapus.',
        OLD."venue_name";
    END IF;

    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prevent_venue_deletion ON "VENUE";
CREATE TRIGGER trg_prevent_venue_deletion
BEFORE DELETE ON "VENUE"
FOR EACH ROW
EXECUTE FUNCTION prevent_venue_deletion();