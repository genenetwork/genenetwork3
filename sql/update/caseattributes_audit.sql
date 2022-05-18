-- metadata_audit.sql ---

-- Copyright (C) 2022  Munyoki Kilyungi <me@bonfacemunyoki.com>

-- Author:  Munyoki Kilyungi <me@bonfacemunyoki.com>

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

-- This table stores data on diffs when editing a case-attribute data
CREATE TABLE caseattributes_audit (
    PRIMARY KEY (id),
    id              INTEGER       AUTO_INCREMENT            NOT NULL,
    status          ENUM('review', 'rejected', 'approved')  NOT NULL,
    editor          VARCHAR(255)                            NOT NULL,
    json_diff_data  VARCHAR(2048)                           NOT NULL,
    time_stamp      timestamp     DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    CHECK (JSON_VALID(json_diff_data))
) CHARACTER SET 'utf8mb4';
