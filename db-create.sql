-- shift_scheduler_test.employee_categories definition

CREATE TABLE `employee_categories` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `level` int DEFAULT NULL,
  `hourly_rate` float DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_employee_categories_name` (`name`),
  KEY `ix_employee_categories_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- shift_scheduler_test.schedules definition

CREATE TABLE `schedules` (
  `id` int NOT NULL AUTO_INCREMENT,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_schedules_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=90 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- shift_scheduler_test.tasks definition

CREATE TABLE `tasks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `description` varchar(255) NOT NULL,
  `status` enum('NOT_STARTED','PENDING','IN_PROGRESS','COMPLETED') NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `title` (`title`),
  KEY `ix_tasks_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- shift_scheduler_test.users definition

CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(255) NOT NULL,
  `full_name` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  KEY `ix_users_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- shift_scheduler_test.work_centers definition

CREATE TABLE `work_centers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `demand` json DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_work_centers_name` (`name`),
  KEY `ix_work_centers_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- shift_scheduler_test.employees definition

CREATE TABLE `employees` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `category_id` int DEFAULT NULL,
  `off_day_preferences` json DEFAULT NULL,
  `shift_preferences` json DEFAULT NULL,
  `work_center_preferences` json DEFAULT NULL,
  `delta` float DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `category_id` (`category_id`),
  KEY `ix_employees_id` (`id`),
  KEY `ix_employees_name` (`name`),
  CONSTRAINT `employees_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `employee_categories` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=50 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- shift_scheduler_test.generated_schedules definition

CREATE TABLE `generated_schedules` (
  `id` int NOT NULL AUTO_INCREMENT,
  `schedule_id` int NOT NULL,
  `employee_id` int NOT NULL,
  `work_center_id` int NOT NULL,
  `shift_start` datetime NOT NULL,
  `shift_end` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `schedule_id` (`schedule_id`),
  KEY `employee_id` (`employee_id`),
  KEY `work_center_id` (`work_center_id`),
  KEY `ix_generated_schedules_id` (`id`),
  CONSTRAINT `generated_schedules_ibfk_1` FOREIGN KEY (`schedule_id`) REFERENCES `schedules` (`id`),
  CONSTRAINT `generated_schedules_ibfk_2` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`),
  CONSTRAINT `generated_schedules_ibfk_3` FOREIGN KEY (`work_center_id`) REFERENCES `work_centers` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=471 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- shift_scheduler_test.shifts definition

CREATE TABLE `shifts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `start_time` datetime NOT NULL,
  `end_time` datetime NOT NULL,
  `employee_id` int NOT NULL,
  `work_center_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `employee_id` (`employee_id`),
  KEY `work_center_id` (`work_center_id`),
  KEY `ix_shifts_id` (`id`),
  CONSTRAINT `shifts_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`),
  CONSTRAINT `shifts_ibfk_2` FOREIGN KEY (`work_center_id`) REFERENCES `work_centers` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=471 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- shift_scheduler_test.schedule_assignments definition

CREATE TABLE `schedule_assignments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `schedule_id` int NOT NULL,
  `shift_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `schedule_id` (`schedule_id`),
  KEY `shift_id` (`shift_id`),
  KEY `ix_schedule_assignments_id` (`id`),
  CONSTRAINT `schedule_assignments_ibfk_1` FOREIGN KEY (`schedule_id`) REFERENCES `schedules` (`id`),
  CONSTRAINT `schedule_assignments_ibfk_2` FOREIGN KEY (`shift_id`) REFERENCES `shifts` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=471 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;