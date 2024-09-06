-- llm_db_update.sql ---

-- Copyright (C) 2024  Alexander kabui <alexanderkabua@gmail.com>

-- Author:  Alexander Kabui <alexanderkabua@gmail.com>

-- This program is free software; you can redistribute it and/or
-- modify it under the terms of the GNU General Public License
-- as published by the Free Software Foundation; either version 3
-- of the License, or (at your option) any later version.

-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU General Public License for more details.

-- You should have received a copy of the GNU General Public License
-- along with this program. If not, see <http://www.gnu.org/licenses/>.

-- Sql file to create the tables for history rating and  adding indexing for the history table
-- this targets setting up a new db
-- and  adding timestamp column the Rating table


CREATE TABLE IF NOT EXISTS history (
    user_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    query TEXT NOT NULL,
    results JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (task_id)
) WITHOUT ROWID;


CREATE INDEX IF NOT EXISTS idx_tbl_history_cols_task_id_user_id
ON history (task_id, user_id);



CREATE TABLE IF NOT EXISTS Rating(
    user_id TEXT NOT NULL,
    query TEXT NOT NULL,
    answer TEXT NOT NULL,
    weight INTEGER NOT NULL DEFAULT 0,
    task_id TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (task_id));
