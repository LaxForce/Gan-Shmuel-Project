--
-- Database: `billdb`
--

CREATE DATABASE IF NOT EXISTS `billdb`;
USE `billdb`;

-- --------------------------------------------------------

--
-- Table structure
--

CREATE TABLE IF NOT EXISTS `Provider` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM  AUTO_INCREMENT=10001 ;

INSERT INTO `Provider` (`name`) VALUES
('Idan'),
('Rony'),
('Itay'),
('Erez'),
('David');

CREATE TABLE IF NOT EXISTS `Rates` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `product_id` varchar(50) NOT NULL,
  `rate` int(11) DEFAULT 0,
  `scope` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY (scope) REFERENCES `Provider`(`id`)
) ENGINE=MyISAM ;

CREATE TABLE IF NOT EXISTS `Trucks` (
  `id` varchar(10) NOT NULL,
  `provider_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`provider_id`) REFERENCES `Provider`(`id`)
) ENGINE=MyISAM ;

INSERT INTO `Trucks` (`id`, `provider_id`) VALUES
( "T-14409", 10001),
("T-17250", 10001),
("T-14045", 10001),
("T-14405", 10002),
("T-16474", 10003),
("T-14964", 10004),
("Truck-A", 10004),
("T-17194", 10005);
--
-- Dumping data
--

/*
INSERT INTO Provider (`name`) VALUES ('ALL'), ('pro1'),
(3, 'pro2');

INSERT INTO Rates (`product_id`, `rate`, `scope`) VALUES ('1', 2, 'ALL'),
(2, 4, 'pro1');

INSERT INTO Trucks (`id`, `provider_id`) VALUES ('134-33-443', 2),
('222-33-111', 1);
*/
