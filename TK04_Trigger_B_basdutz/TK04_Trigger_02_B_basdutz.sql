-- Mencegah duplikasi nama Venue di kota yang sama (ignore case):
-- Saat Pengguna (Admin atau Organizer) ingin mendaftarkan Venue baru atau memperbarui nama Venue, sistem akan mengecek apakah sudah terdapat duplikasi (tanpa memperhatikan besar-kecilnya huruf) pada nama_venue di dalam kota yang sama. Jika ada duplikasi, sistem akan mencegah pendaftaran dan memberikan pesan error, yaitu:
-- "Venue <nama venue>'di kota '<nama kota>'sudah terdaftar dengan ID <id_venue>."
-- Contoh output error:
-- ERROR: Venue "Gelora Bung Karno" di kota "Jakarta" sudah terdaftar dengan ID d4ua-ed4e-41e2-bc8b-e7495.
CREATE OR REPLACE FUNCTION check_duplicate_venue()
RETURNS TRIGGER AS $$
DECLARE
    existing_id UUID;
    existing_kota TEXT;
BEGIN
    SELECT v.id_venue, k.nama_kota
    INTO existing_id, existing_kota
    FROM venue v
    JOIN kota k ON v.id_kota = k.id_kota
    WHERE LOWER(v.nama_venue) = LOWER(NEW.nama_venue)
      AND v.id_kota = NEW.id_kota
      AND v.id_venue <> COALESCE(NEW.id_venue, '')
    LIMIT 1;

    IF existing_id IS NOT NULL THEN
        RAISE EXCEPTION
        'Venue "%" di kota "%" sudah terdaftar dengan ID %.',
        NEW.nama_venue,
        existing_kota,
        existing_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_check_duplicate_venue
BEFORE INSERT OR UPDATE ON venue
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
        FROM event
        WHERE id_venue = OLD.id_venue
          AND (
                tanggal_event >= CURRENT_DATE
                OR LOWER(status_event) = 'sedang berlangsung'
              )
    ) THEN
        RAISE EXCEPTION
        'Venue "%" masih memiliki event aktif sehingga tidak dapat dihapus.',
        OLD.nama_venue;
    END IF;

    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_prevent_venue_deletion
BEFORE DELETE ON venue
FOR EACH ROW
EXECUTE FUNCTION prevent_venue_deletion();