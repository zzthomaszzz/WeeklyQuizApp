-- WeeklyQuizApp sample user accounts
-- TEST AND DEVELOPMENT DATABASES ONLY. Never run against production.
--
-- Run this before seed.sql, which looks these accounts up by email.
-- Every account below uses the password: demo-password-2026
-- The hashes are bcrypt. The password is deliberately public so that a
-- clean clone can be seeded. It must never be reused anywhere real.

BEGIN;

INSERT INTO users (email, name, password_hash, role) VALUES
    ('lecturer.demo@example.com', 'Demo Lecturer', '$2b$12$n4jZz3oCCsqO8lJHtNiYn.DLlLq4o6lfz53YYM8AGaANdikzpadJu', 'lecturer'),
    ('student1.demo@example.com', 'Demo Student One', '$2b$12$vi3hMbdzI.0mqxSIN9NuTe8a6LLExsArWyb6AiQrzO2OzfFG.ts5q', 'student'),
    ('student2.demo@example.com', 'Demo Student Two', '$2b$12$SF2xwnR.4p5WkEodkCVOueObpWgCRyhSl2XZoNL7RW9ona59/3qV2', 'student'),
    ('james.wilson.demo@example.com', 'James Wilson', '$2b$12$WrGB/sMDx1XXgwnv/XUoe.tGZxoZao3tow452p7Lf0rmKYyahZrdq', 'student'),
    ('mei.chen.demo@example.com', 'Mei Chen', '$2b$12$UxdHcwKpoXYKZrx21VXhKe5TK/6xlz6WmkcboUAjXEC.vWC50YMjq', 'student'),
    ('haruto.sato.demo@example.com', 'Haruto Sato', '$2b$12$wnzfu0hYlsf733blG21yQ.4lxRjkBNxJucXln26VceDKFdeLHNCu2', 'student'),
    ('aisha.rahman.demo@example.com', 'Aisha Rahman', '$2b$12$ktkTT6rtK9KtmSEPyygT6O3zZE/MgYucH/BdU4gV9V2YJSHtKmAwy', 'student'),
    ('minjun.park.demo@example.com', 'Minjun Park', '$2b$12$ZnDNBq2JYwzx6mHHB.zUY.2dl83Y5CL7y/vcisK1AFlRrpD7T0Euq', 'student'),
    ('anika.patel.demo@example.com', 'Anika Patel', '$2b$12$yACU1ooBsGHQHeasISq3/uclVunNgTnpbhZqT6vGDk6oRR7jSkzYy', 'student'),
    ('daniel.reyes.demo@example.com', 'Daniel Reyes', '$2b$12$wHVtWLfOZ0fvqpLVSUbDVu3rGS3xzxF0RYQPw7ov8eglFhgTZfNxG', 'student'),
    ('sophia.martinez.demo@example.com', 'Sophia Martinez', '$2b$12$c8IjGwZj8esolyCSdVi/xO2fVCZa2pLj7vL.ZVuGWzKhDrU0F/nXa', 'student')
ON CONFLICT (email) DO NOTHING;

COMMIT;
