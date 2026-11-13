import time
from pathlib import Path

from app.pipeline import ask

# (no, pertanyaan, kategori, dokumen_harapan, kata_kunci_wajib)
KASUS = [
    (1, "Berapa hari cuti tahunan pegawai tetap?", "Satu dokumen", "kebijakan_cuti.md", ["12 hari"]),
    (2, "Berapa lama batas waktu pengajuan reimbursement?", "Satu dokumen", "prosedur_reimbursement.md", ["14 hari"]),
    (3, "Jam berapa IT Helpdesk melayani?", "Satu dokumen", "sop_it_helpdesk.md", ["08.00", "17.00"]),
    (4, "Berapa hari maksimal WFH dalam seminggu?", "Satu dokumen", "kebijakan_wfh.md", ["2 hari"]),
    (5, "Berapa nilai maksimal hadiah dari vendor yang boleh diterima?", "Satu dokumen", "kode_etik.md", ["500.000"]),
    (6, "Berapa lama masa probation?", "Satu dokumen", "panduan_onboarding.md", ["3 bulan"]),
    (7, "Apa saja yang diterima pegawai baru di hari pertama, termasuk akses IT dan hak cuti?", "Lintas dokumen", "panduan_onboarding.md", ["laptop", "VPN"]),
    (8, "Kalau WFH, apa yang wajib dipakai dan biaya internet apa yang bisa diklaim?", "Lintas dokumen", "kebijakan_wfh.md", ["VPN", "100.000"]),
    (9, "Apakah pegawai baru yang masih probation boleh WFH dan ambil cuti tahunan?", "Lintas dokumen", "panduan_onboarding.md", ["WFH", "cuti tahunan"]),
    (10, "Kalau mau ngajuin cuti harus kapan?", "Bahasa tidak baku", "kebijakan_cuti.md", ["7 hari"]),
    (11, "Lupa password, harus gimana ya?", "Bahasa tidak baku", "sop_it_helpdesk.md", ["MFA"]),
    (12, "Berapa gaji pokok seorang manajer?", "Tidak ada", None, []),
    (13, "Kapan THR dibayarkan?", "Tidak ada", None, []),
    (14, "Siapa CEO perusahaan ini?", "Tidak ada", None, []),
    (15, "Bagaimana cara memasak nasi goreng?", "Tidak ada", None, []),
]


def ya(x):
    return "Ya" if x else "Tidak"


baris = []
lulus = jawaban_benar = sumber_tepat = ditolak_benar = 0
n_ada = n_tidak = 0
total_latensi = 0

for no, tanya, kategori, dok, kata_kunci in KASUS:
    h = ask(tanya)
    total_latensi += h["latency_ms"]
    docs = {s["document"] for s in h["sources"]}

    if dok:  # seharusnya dijawab
        n_ada += 1
        j_ok = h["grounded"] and all(k.lower() in h["answer"].lower() for k in kata_kunci)
        s_ok = dok in docs
        status = h["grounded"] and j_ok and s_ok
        jawaban_benar += j_ok
        sumber_tepat += s_ok
        kolom_j, kolom_s = ya(j_ok), ya(s_ok)
    else:  # seharusnya ditolak
        n_tidak += 1
        t_ok = not h["grounded"]
        status = t_ok
        ditolak_benar += t_ok
        kolom_j, kolom_s = "-", "-"

    lulus += bool(status)
    baris.append(
        f"| {no} | {kategori} | {tanya} | {'Dijawab' if h['grounded'] else 'Ditolak'} "
        f"| {h['top_score']} | {kolom_j} | {kolom_s} | {h['latency_ms']} | {'PASS' if status else 'FAIL'} |"
    )
    print(f"#{no} {'PASS' if status else 'FAIL'}")
    if h["grounded"]:
        time.sleep(4)  # hindari batas request per menit

ringkasan = [
    f"- Lulus keseluruhan: **{lulus}/{len(KASUS)}**",
    f"- Jawaban benar (kata kunci): **{jawaban_benar}/{n_ada}**",
    f"- Sumber tepat: **{sumber_tepat}/{n_ada}**",
    f"- Pertanyaan di luar dokumen ditolak: **{ditolak_benar}/{n_tidak}**",
    f"- Rata-rata latensi: **{total_latensi // len(KASUS)} ms**",
]

isi = (
    "# Hasil Evaluasi\n\n"
    "| No | Kategori | Pertanyaan | Hasil | Skor | Jawaban benar | Sumber tepat | Latensi (ms) | Status |\n"
    "|---|---|---|---|---|---|---|---|---|\n"
    + "\n".join(baris)
    + "\n\n## Ringkasan\n\n" + "\n".join(ringkasan) + "\n"
)
Path("tests/hasil_evaluasi.md").write_text(isi, encoding="utf-8")
print("\n" + "\n".join(ringkasan))
print("\nTabel lengkap: tests/hasil_evaluasi.md")