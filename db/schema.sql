drop table if exists article;
create table article (
	id integer primary key autoincrement,
	time timestamp not null default (datetime('now','localtime')),
	title string not null,
	slug string unique,
	file string not null,
	html text
);