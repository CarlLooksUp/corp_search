CREATE TABLE corp_name (
	ID varchar(20) CONSTRAINT id_key PRIMARY KEY,
	name varchar(512) NOT NULL,
	address varchar(2048),
	org_date date,
	exact_name varchar(2048),
	org_type varchar(2048),
	profile_url varchar(2048)
);
