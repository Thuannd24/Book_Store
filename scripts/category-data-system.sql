-- 1. Đảm bảo chọn đúng Database catalog_db trước khi chạy
-- 2. Chạy lệnh INSERT vào bảng public.categories

INSERT INTO public.categories (id, name, slug, description, is_active, created_at) VALUES 
(5, 'Tâm lý - Kỹ năng sống', 'tam-ly-ky-nang-song', 'Sách tâm lý học và phát triển bản thân', true, '2026-03-18 07:23:50'),
(6, 'Lịch sử', 'lich-su', 'Sách lịch sử Việt Nam và thế giới', true, '2026-03-18 07:23:50'),
(7, 'Công nghệ thông tin', 'cong-nghe-thong-tin', 'Sách lập trình và công nghệ', true, '2026-03-18 07:23:50'),
(8, 'Thiếu nhi', 'thieu-nhi', 'Sách dành cho trẻ em và thiếu niên', true, '2026-03-18 07:23:50'),
(9, 'Manga - Comic', 'manga-comic', 'Truyện tranh Manga và Comic', true, '2026-03-18 07:23:50'),
(10, 'Ngoại ngữ', 'ngoai-ngu', 'Sách học ngoại ngữ', true, '2026-03-18 07:23:50');

-- 3. Cập nhật lại Sequence để không bị lỗi Duplicate Key khi thêm mới sau này
SELECT pg_catalog.setval('public.categories_id_seq', 10, true);