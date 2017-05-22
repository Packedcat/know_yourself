-- schema.sql

drop database if exists awesome;

create database awesome;

use awesome;

grant select, insert, update, delete on awesome.* to 'yoite'@'localhost' identified by '71546';

create table users (
    `id` varchar(50) not null,
    `email` varchar(50) not null,
    `passwd` varchar(50) not null,
    `admin` bool not null,
    `name` varchar(50) not null,
    `image` varchar(500) not null,
    `created_at` real not null,
    unique key `idx_email` (`email`),
    key `idx_created_at` (`created_at`),
    primary key (`id`)
) engine=innodb default charset=utf8;

create table record (
    `id` varchar(50) not null,
    `user_id` varchar(50) not null,
    `genres` varchar(50) not null,
    `title` varchar(50),
    `content` mediumtext not null,
    `trash` bool not null,
    `archive` bool not null,
    `is_delete` bool not null,
    `created_at` real not null,
    key `idx_created_at` (`created_at`),
    primary key (`id`)
) engine=innodb default charset=utf8;

create table tags (
    `id` varchar(50) not null,
    `tag` varchar(50) not null,
    `user_id` varchar(50) not null,
    `created_at` real not null,
    key `idx_created_at` (`created_at`),
    primary key (`id`)
) engine=innodb default charset=utf8;

create table relationship (
    `id` varchar(50) not null,
    `tag` varchar(50) not null,
    `tag_id` varchar(50) not null,
    `record_id` varchar(50) not null,
    `created_at` real not null,
    key `idx_created_at` (`created_at`),
    primary key (`id`)
) engine=innodb default charset=utf8;
