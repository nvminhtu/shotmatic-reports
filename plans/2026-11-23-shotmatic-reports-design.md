# ShotMatic Reports — design (2026-11-23)

Status: duyệt thiết kế 2026-11-23 (Tu: "Duyệt, GitHub Pages"). Spec này chờ Tu đọc lại trước khi lên plan code.

## Mục tiêu

Tu chụp màn hình 1 kết quả research trong ShotMatic → gõ `/shotmatic-report` → trong vài phút có:

1. Hình đã gắn logo `shotmatic.app`, tên file chứa long-tail keyword.
2. 1 bài tiếng Anh trên web report (MkDocs Material, GitHub Pages), nằm đúng nhóm trong sidebar.
3. 1 caption X tiếng Anh (≤ 280 ký tự, có link bài) để Tu tự copy và bấm Post.

Đo thành công: 1 hình → bài live + caption trong 1 lần chạy, không phải sửa tay.

## Không làm (YAGNI)

- Không tự đăng X, không gọi API X.
- Không Mac app / web upload riêng, không gọi API AI riêng — Claude viết nội dung.
- Không comment, không tìm kiếm nâng cao ngoài search sẵn của MkDocs Material.

## Nơi đặt

- Repo: `shotmatic-reports` (folder này). Push lên GitHub, bật Pages → `https://<owner>.github.io/shotmatic-reports/`.
- Owner: hỏi Tu trước lần push đầu (`gh` đang đăng nhập `tucarmd`; site docs cũ nằm dưới `nvminhtu`).
- Deploy: GitHub Actions build `mkdocs build` → Pages (không commit `site/`).
- Skill: `~/.claude/skills/shotmatic-report/` (SKILL.md + scripts), đường dẫn repo ghi trong SKILL.md.

## Cấu trúc repo

```
shotmatic-reports/
  mkdocs.yml                  # copy khung niche-radar-docs: theme material, logo, font Figtree, sáng/tối, tiếng Anh
  docs/
    index.md                  # danh sách bài mới nhất theo ngày (tự sinh)
    images/                   # logo, favicon (copy từ niche-radar-docs)
    trend/  hunt-app/  keyword/  aso/  review/  youtube/   # mỗi loại 1 thư mục
      index.md                # trang nhóm (tự sinh)
      2026-11-23-speaker-cleaner-keyword-ranks.md
      img/shotmatic.app-speaker-cleaner-keyword-ranks-2026-11-23.png
  scripts/
    watermark.py              # gắn logo + đặt tên
    new_post.py               # tạo file .md từ mẫu + cập nhật nav/index
    check_post.py             # soát bài trước khi push
  tests/                      # pytest cho 3 script
  inbox/                      # Tu có thể thả hình vào đây (gitignore)
  .github/workflows/pages.yml
```

Loại tính năng (thư mục) ban đầu: `trend`, `hunt-app`, `keyword`, `aso`, `review`, `youtube`. Thêm loại mới = thêm 1 dòng trong `scripts/types.json`.

## Sidebar + trang chủ

- Sidebar: nhóm theo loại (Trend / Hunt App / Keyword / …), trong nhóm bài mới nhất ở trên, nhãn bài = `Nov 23 · Speaker cleaner keyword ranks`.
- Nav do `new_post.py` sinh lại từ frontmatter mọi bài (không sửa tay `mkdocs.yml` nav).
- Trang chủ: danh sách 1 cột theo ngày (ngày → bài, chip loại). Không chia cột thẻ hẹp (luật trang đọc của Tu); soát ở ~1340px.

## Đặt tên

- Slug = long-tail keyword + kiểu kết quả, chữ thường, gạch nối, ≤ 60 ký tự: `speaker-cleaner-keyword-ranks`.
- Hình: `shotmatic.app-<slug>-<YYYY-MM-DD>.png`.
- Bài: `docs/<type>/<YYYY-MM-DD>-<slug>.md`. Trùng tên → thêm `-2`.

## watermark.py

- Vào: đường dẫn hình (png/jpg/webp), slug, ngày. Ra: PNG trong `docs/<type>/img/`.
- Góc dưới phải: favicon ShotMatic + chữ `shotmatic.app`, trên viên nền trắng bo góc mờ ~85%, lề 2% cạnh ngắn. Cao logo ≈ 4% chiều cao hình (tối thiểu 28px, tối đa 64px).
- Không thu nhỏ hình gốc; nếu rộng > 2400px thì thu về 2400px (cho X + web nhẹ).
- Lỗi: file không phải ảnh / không mở được → thoát mã 1 kèm thông báo rõ.

## Bài viết (frontmatter + khung)

```yaml
---
title: "Top 10 speaker cleaner apps on the App Store — keyword ranks"
date: 2026-11-23
type: keyword
keyword: speaker cleaner
image: img/shotmatic.app-speaker-cleaner-keyword-ranks-2026-11-23.png
source: "ShotMatic Keyword ranks, US App Store, measured 2026-11-23"
x_caption: "..."
---
```

Thân bài: **The short answer** (40–60 từ) → hình (alt text có keyword) → **What the data shows** (3–5 gạch đầu dòng, mỗi số có nguồn) → **What this means if you build in this niche** (2–3 câu) → **How this was measured** (tính năng ShotMatic, store, nước, ngày) → nút "Try ShotMatic free" về `https://shotmatic.app`.

Quy tắc số: chỉ dùng số đọc được trên hình hoặc lấy từ ShotMatic MCP (niche-radar) kèm nguồn; thiếu thì ghi "not measured". Không bịa.

## Caption X

≤ 280 ký tự tính cả link (link tính 23 ký tự), 1 câu móc + 1–2 số + link bài, tối đa 2 hashtag. Lưu vào frontmatter `x_caption` và in ra cuối lượt chạy cùng đường dẫn hình đã gắn logo.

## check_post.py

Báo lỗi (thoát 1) khi: thiếu frontmatter bắt buộc, `type` không có trong types.json, hình không tồn tại hoặc tên sai mẫu, thiếu "The short answer" hoặc dài ngoài 40–80 từ, thiếu "How this was measured", caption X > 280 ký tự.

## Luồng skill /shotmatic-report

1. Lấy hình: hình Tu vừa dán vào chat (đường dẫn ảnh tạm) hoặc file mới nhất trong `inbox/`.
2. Claude đọc hình → đề xuất `type`, keyword, slug, tiêu đề (Tu có gợi ý thì theo gợi ý).
3. Thử ShotMatic MCP để thêm số cùng keyword; MCP không chạy thì chỉ dùng số trên hình.
4. `watermark.py` → `new_post.py` → Claude viết thân bài + caption → `check_post.py`.
5. `mkdocs build --strict`, mở bản build ở ~1340px xem tận mắt.
6. Commit `post(<type>): <slug>` + push → Actions deploy.
7. In ra: link bài, đường dẫn hình gắn logo, caption X.

## Kiểm thử

- pytest: watermark (kích thước, vị trí logo, tên file, thu ảnh > 2400px, file hỏng), new_post (slug, trùng tên, nav đúng thứ tự), check_post (từng lỗi).
- Chạy thật 1 lần với hình "Keyword ranks — speaker cleaner" Tu gửi 2026-11-23.
