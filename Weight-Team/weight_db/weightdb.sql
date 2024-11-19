--
-- Database: `Weight`
--

CREATE DATABASE IF NOT EXISTS `weight`;

-- --------------------------------------------------------

--
-- Table structure for table `containers_registered`
--

USE weight;

CREATE TABLE IF NOT EXISTS `containers_registered` (
  `container_id` varchar(15) NOT NULL,
  `weight` int(12) DEFAULT NULL,
  `unit` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`container_id`)
) ENGINE=MyISAM;

-- Insert sample data for `containers_registered`

INSERT INTO `containers_registered` (`container_id`, `weight`, `unit`) VALUES
('C-35434', 296, 'kg'),
('C-73281', 273, 'kg'),
('C-35537', 292, 'kg'),
('C-49036', 272, 'kg'),
('C-85957', 274, 'kg'),
('C-57132', 306, 'kg'),
('C-80015', 285, 'kg'),
('C-40162', 255, 'kg'),
('C-66667', 238, 'kg'),
('C-65481', 306, 'kg'),
('C-65816', 270, 'kg'),
('C-38068', 267, 'kg'),
('C-36882', 286, 'kg'),
('C-38559', 253, 'kg'),
('C-83754', 247, 'kg'),
('C-40277', NULL, 'kg'),
('C-55516', 260, 'kg'),
('C-45237', 301, 'kg'),
('C-69828', 269, 'kg'),
('C-44997', 250, 'kg'),
('C-52273', 308, 'kg'),
('C-63478', 245, 'kg'),
('C-42418', NULL, 'kg'),
('C-86865', 299, 'kg'),
('C-38552', 266, 'kg'),
('C-81185', 242, 'kg'),
('C-71151', 300, 'kg'),
('C-78131', 273, 'kg'),
('C-61969', 289, 'kg'),
('C-82193', 308, 'kg'),
('C-85358', 259, 'kg'),
('C-47634', 285, 'kg'),
('C-83570', 278, 'kg'),
('C-45628', 288, 'kg'),
('C-70986', 251, 'kg'),
('C-54804', NULL, 'kg'),
('K-8263', 666, 'lbs'),
('K-5269', 666, 'lbs'),
('K-7943', 644, 'lbs'),
('K-5355', 642, 'lbs'),
('K-8120', 657, 'lbs'),
('K-4987', 653, 'lbs'),
('K-5867', 666, 'lbs'),
('K-3963', NULL, 'lbs'),
('K-8298', 554, 'lbs'),
('K-4722', 530, 'lbs'),
('K-7947', 589, 'lbs'),
('K-6176', 523, 'lbs'),
('K-3690', 682, 'lbs'),
('K-7488', 633, 'lbs'),
('K-8128', 528, 'lbs'),
('K-4743', 572, 'lbs'),
('K-6350', NULL, 'lbs'),
('K-7425', 677, 'lbs'),
('K-7714', 525, 'lbs'),
('K-4109', 587, 'lbs'),
('K-5768', 569, 'lbs');

-- --------------------------------------------------------

--
-- Table structure for table `transactions`
--

CREATE TABLE IF NOT EXISTS `transactions` (
  `sessionId` varchar(20) NOT NULL,
  `id` int(12) NOT NULL AUTO_INCREMENT,
  `datetime` datetime DEFAULT NULL,
  `direction` varchar(10) DEFAULT NULL,
  `truck` varchar(50) DEFAULT NULL,
  `containers` varchar(10000) DEFAULT NULL,
  `bruto` int(12) DEFAULT NULL,
  `truckTara` int(12) DEFAULT NULL,
  `neto` int(12) DEFAULT NULL,
  `produce` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=10001;

-- Insert sample data for `transactions`

INSERT INTO transactions (sessionId, id, datetime, direction, truck, containers, bruto, truckTara, neto, produce) VALUES
(101, 10001, '2024-11-16 08:00:00', 'in', 'T-14409', 'C-35434,C-73281', 5600, 3000, 2600, 'apples'),
(101, 10002, '2024-11-16 09:15:00', 'out', 'T-14409', NULL, NULL, 3000, NULL, 'apples'),
(102, 10003, '2024-11-16 09:45:00', 'in', 'T-16474', 'C-35537', 5500, 3200, 2300, 'oranges'),
(103, 10004, '2024-11-16 10:00:00', 'in', 'T-14964', 'K-8263', 5800, 3300, 2500, 'bananas'),
(103, 10005, '2024-11-16 11:30:00', 'out', 'T-14964', NULL, NULL, 3300, NULL, 'bananas'),
(102, 10006, '2024-11-16 12:00:00', 'out', 'T-16474', NULL, NULL, 3200, NULL, 'oranges'),
(104, 10007, '2024-11-16 12:30:00', 'in', 'T-17194', 'C-49036', 6100, 3400, 2700, 'grapes'),
(104, 10008, '2024-11-16 13:15:00', 'out', 'T-17194', NULL, NULL, 3400, NULL, 'grapes'),
(105, 10009, '2024-11-16 13:45:00', 'in', 'T-17250', 'K-5269,K-7943', 6200, 3500, 2700, 'watermelons'),
(106, 10010, '2024-11-16 14:10:00', 'in', 'T-14045', 'C-57132,C-80015', 6300, 3600, 2700, 'mangoes'),
(106, 10011, '2024-11-16 15:30:00', 'out', 'T-14045', NULL, NULL, 3600, NULL, 'mangoes'),
(107, 10012, '2024-11-16 16:00:00', 'in', 'T-14263', 'C-65481,C-66667', 5900, 3100, 2800, 'peaches'),
(108, 10013, '2024-11-16 16:20:00', 'in', 'T-17164', 'K-7947', 5200, 2900, 2300, 'strawberries'),
(107, 10014, '2024-11-16 17:15:00', 'out', 'T-14263', NULL, NULL, 3100, NULL, 'peaches'),
(109, 10015, '2024-11-16 17:30:00', 'in', 'T-16810', 'K-8120,K-4987', 5500, 3200, 2300, 'apples'),
(108, 10016, '2024-11-16 18:00:00', 'out', 'T-17164', NULL, NULL, 2900, NULL, 'strawberries'),
(110, 10017, '2024-11-16 18:30:00', 'in', 'T-17077', 'C-40277,C-45237', 6000, 3500, 2500, 'bananas'),
(110, 10018, '2024-11-16 19:30:00', 'out', 'T-17077', NULL, NULL, 3500, NULL, 'bananas'),
(111, 10019, '2024-11-16 20:00:00', 'in', 'T-13972', 'C-38552', 5100, 2600, 2500, 'mangoes'),
(112, 10020, '2024-11-16 20:30:00', 'in', 'T-13982', 'K-5867,K-3963', 5800, 3100, 2700, 'grapes'),
(113, 10021, '2024-11-16 21:00:00', 'in', 'T-15689', 'K-3690', 5700, 3000, 2700, 'watermelons'),
(111, 10022, '2024-11-16 21:15:00', 'out', 'T-13972', NULL, NULL, 2600, NULL, 'mangoes'),
(114, 10023, '2024-11-16 21:45:00', 'in', 'T-14664', 'K-7488,K-8128', 6300, 3400, 2900, 'peaches'),
(114, 10024, '2024-11-16 22:30:00', 'out', 'T-14664', NULL, NULL, 3400, NULL, 'peaches'),
(115, 10025, '2024-11-16 23:00:00', 'in', 'T-14623', 'C-57132,C-65481', 6400, 3700, 2700, 'oranges'),
(115, 10026, '2024-11-16 23:45:00', 'out', 'T-14623', NULL, NULL, 3700, NULL, 'oranges'),
(116, 10027, '2024-11-17 00:30:00', 'in', 'T-14873', 'C-55237', 6200, 3400, 2800, 'bananas'),
(117, 10028, '2024-11-17 01:00:00', 'in', 'T-14064', 'C-69828', 6000, 3200, 2800, 'grapes'),
(117, 10029, '2024-11-17 01:45:00', 'out', 'T-14064', NULL, NULL, 3200, NULL, 'grapes'),
(118, 10030, '2024-11-17 02:00:00', 'in', 'T-13799', 'C-52273', 5500, 3100, 2400, 'apples'),
(118, 10031, '2024-11-17 02:45:00', 'out', 'T-13799', NULL, NULL, 3100, NULL, 'apples'),
(119, 10032, '2024-11-17 03:15:00', 'in', 'T-15861', 'C-63478', 5700, 3200, 2500, 'peaches'),
(119, 10033, '2024-11-17 04:00:00', 'out', 'T-15861', NULL, NULL, 3200, NULL, 'peaches'),
(120, 10034, '2024-11-17 04:30:00', 'in', 'T-16584', 'K-7425', 6300, 3600, 2700, 'mangoes'),
(121, 10035, '2024-11-17 05:00:00', 'in', 'T-17267', 'K-7714', 6200, 3500, 2700, 'bananas'),
(120, 10036, '2024-11-17 05:45:00', 'out', 'T-16584', NULL, NULL, 3600, NULL, 'mangoes'),
(122, 10037, '2024-11-17 06:00:00', 'in', 'T-16617', 'C-52463', 6400, 3700, 2700, 'grapes'),
(122, 10038, '2024-11-17 06:45:00', 'out', 'T-16617', NULL, NULL, 3700, NULL, 'grapes'),
(121, 10039, '2024-11-17 07:15:00', 'out', 'T-17267', NULL, NULL, 3500, NULL, 'bananas'),
(123, 10040, '2024-11-17 07:30:00', 'in', 'T-16270', 'C-40162,C-47634', 6400, 3700, 2700, 'oranges');

-- --------------------------------------------------------

--
-- Show tables and describe
--

SHOW TABLES;

DESCRIBE containers_registered;
DESCRIBE transactions;

