-- metadata_audit.sql ---

-- Copyright (C) 2021 Bonface Munyoki K. <me@bonfacemunyoki.com>

-- Author: Bonface Munyoki K. <me@bonfacemunyoki.com>

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

-- This table stores data on diffs when editing a Published dataset's data
CREATE TABLE metadata_audit (
    PRIMARY KEY (id),
    id              INTEGER       AUTO_INCREMENT            NOT NULL,
    dataset_id      INTEGER                                 NOT NULL,
    editor          VARCHAR(255)                            NOT NULL,
    json_diff_data  VARCHAR(2048)                           NOT NULL,
    time_stamp      timestamp     DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    CHECK (JSON_VALID(json_diff_data))
) CHARACTER SET 'utf8mb4';
