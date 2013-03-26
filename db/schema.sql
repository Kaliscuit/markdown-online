drop table if exists article;
create table article (
	id integer primary key autoincrement,
	time timestamp not null default (datetime('now','localtime')),
	title string not null,
	slug string unique not null,
	category int not null default 0,
	file string not null,
	html text
);