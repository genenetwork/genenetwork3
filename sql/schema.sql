-- This is a work-in-progress schema for the GeneNetwork database. The
-- GeneNetwork database has no foreign key constraint information. This schema
-- has them manually added. But, the work is not complete, and there may be
-- errors. A visualization of this schema can be found in schema.png and
-- schema.svg.

-- MySQL dump 10.16  Distrib 10.1.41-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: db_webqtl
-- ------------------------------------------------------
-- Server version	10.5.8-MariaDB-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `AccessLog`
--

DROP TABLE IF EXISTS `AccessLog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `AccessLog` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `accesstime` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `ip_address` char(20) NOT NULL DEFAULT '0.0.0.0',
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=1366832 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `AvgMethod`
--

DROP TABLE IF EXISTS `AvgMethod`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `AvgMethod` (
  `Id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `AvgMethodId` int(5) DEFAULT NULL,
  `Name` char(30) NOT NULL DEFAULT '',
  `Normalization` varchar(30) DEFAULT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=MyISAM AUTO_INCREMENT=28 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `BXDSnpPosition`
--

DROP TABLE IF EXISTS `BXDSnpPosition`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `BXDSnpPosition` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `Chr` char(2) DEFAULT NULL,
  `StrainId1` int(11) DEFAULT NULL,
  `StrainId2` int(11) DEFAULT NULL,
  `Mb` double DEFAULT NULL,
  `Mb_2016` double DEFAULT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY (StrainId1) REFERENCES Strain(Id),
  FOREIGN KEY (StrainId2) REFERENCES Strain(Id),
  KEY `BXDSnpPosition` (`Chr`,`StrainId1`,`StrainId2`,`Mb`)
) ENGINE=MyISAM AUTO_INCREMENT=7791982 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `CaseAttribute`
--

DROP TABLE IF EXISTS `CaseAttribute`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `CaseAttribute` (
  `Id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `Name` varchar(30) NOT NULL DEFAULT '',
  PRIMARY KEY (`Id`)
) ENGINE=MyISAM AUTO_INCREMENT=34 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `CaseAttributeXRef`
--

DROP TABLE IF EXISTS `CaseAttributeXRef`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `CaseAttributeXRef` (
  `ProbeSetFreezeId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `StrainId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `CaseAttributeId` smallint(5) NOT NULL DEFAULT 0,
  `Value` varchar(100) NOT NULL DEFAULT '',
  PRIMARY KEY (`ProbeSetFreezeId`,`StrainId`,`CaseAttributeId`),
  FOREIGN KEY (ProbeSetFreezeId) REFERENCES ProbeSetFreeze(Id),
  FOREIGN KEY (StrainId) REFERENCES Strain(Id),
  FOREIGN KEY (CaseAttributeId) REFERENCES CaseAttribute(Id)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `CaseAttributeXRefNew`
--

DROP TABLE IF EXISTS `CaseAttributeXRefNew`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `CaseAttributeXRefNew` (
  `InbredSetId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `StrainId` int(8) unsigned NOT NULL DEFAULT 0,
  `CaseAttributeId` smallint(5) NOT NULL DEFAULT 0,
  `Value` varchar(100) NOT NULL DEFAULT '',
  PRIMARY KEY (`InbredSetId`,`StrainId`,`CaseAttributeId`),
  FOREIGN KEY (InbredSetId) REFERENCES InbredSet(InbredSetId),
  FOREIGN KEY (StrainId) REFERENCES Strain(Id),
  FOREIGN KEY (CaseAttributeId) REFERENCES CaseAttribute(Id)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `CeleraINFO_mm6`
--

DROP TABLE IF EXISTS `CeleraINFO_mm6`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `CeleraINFO_mm6` (
  `Id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `SNPID` char(14) NOT NULL DEFAULT '',
  `chromosome` char(3) DEFAULT NULL,
  `MB_UCSC` double DEFAULT NULL,
  `MB_celera` double DEFAULT NULL,
  `allele_B6` char(4) DEFAULT NULL,
  `allele_D2` char(4) DEFAULT NULL,
  `allele_AJ` char(4) DEFAULT NULL,
  `B6_D2` char(1) DEFAULT NULL,
  `B6_AJ` char(1) DEFAULT NULL,
  `D2_AJ` char(1) DEFAULT NULL,
  `MB_UCSC_OLD` double DEFAULT NULL,
  `allele_S1` char(4) DEFAULT NULL,
  `allele_X1` char(4) DEFAULT NULL,
  `flanking5` char(100) DEFAULT NULL,
  `flanking3` char(100) DEFAULT NULL,
  PRIMARY KEY (`Id`),
  KEY `celeraIndex` (`chromosome`,`MB_celera`),
  KEY `celeraIndex2` (`chromosome`,`MB_UCSC`),
  KEY `chromosome_2` (`chromosome`,`MB_UCSC`),
  KEY `MB_UCSC_2` (`MB_UCSC`,`chromosome`),
  KEY `SNPID` (`SNPID`)
) ENGINE=MyISAM AUTO_INCREMENT=3028848 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Chr_Length`
--

DROP TABLE IF EXISTS `Chr_Length`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Chr_Length` (
  `Name` char(3) NOT NULL DEFAULT '',
  `SpeciesId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `OrderId` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `Length` int(10) unsigned NOT NULL DEFAULT 0,
  `Length_2016` int(10) unsigned NOT NULL DEFAULT 0,
  `Length_mm8` int(10) unsigned DEFAULT NULL,
  UNIQUE KEY `nameIdx` (`SpeciesId`,`Name`),
  UNIQUE KEY `SpeciesIdx` (`SpeciesId`,`OrderId`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `DBList`
--

DROP TABLE IF EXISTS `DBList`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `DBList` (
  `Id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `DBTypeId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `FreezeId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `Name` char(50) NOT NULL DEFAULT '',
  `Code` char(50) DEFAULT NULL,
  PRIMARY KEY (`Id`),
  UNIQUE KEY `Cde` (`Code`),
  FOREIGN KEY (DBTypeId) REFERENCES DBType(Id),
  KEY `DBIndex` (`DBTypeId`,`FreezeId`)
) ENGINE=MyISAM AUTO_INCREMENT=907 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `DBType`
--

DROP TABLE IF EXISTS `DBType`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `DBType` (
  `Id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `Name` char(30) NOT NULL DEFAULT '',
  PRIMARY KEY (`Id`)
) ENGINE=MyISAM AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `DatasetMapInvestigator`
--

DROP TABLE IF EXISTS `DatasetMapInvestigator`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `DatasetMapInvestigator` (
  `Id` mediumint(9) NOT NULL AUTO_INCREMENT,
  `DatasetId` int(6) NOT NULL,
  `InvestigatorId` int(6) NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=MyISAM AUTO_INCREMENT=2403 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `DatasetStatus`
--

DROP TABLE IF EXISTS `DatasetStatus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `DatasetStatus` (
  `DatasetStatusId` int(5) NOT NULL,
  `DatasetStatusName` varchar(20) DEFAULT NULL,
  UNIQUE KEY `DatasetStatusId` (`DatasetStatusId`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Dataset_mbat`
--

DROP TABLE IF EXISTS `Dataset_mbat`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Dataset_mbat` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `switch` int(1) DEFAULT NULL,
  `species` varchar(255) DEFAULT NULL,
  `cross` varchar(255) DEFAULT NULL,
  `tissue` varchar(255) DEFAULT NULL,
  `database` varchar(255) DEFAULT NULL,
  `database_LongName` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=16 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Datasets`
--

DROP TABLE IF EXISTS `Datasets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Datasets` (
  `DatasetId` int(6) NOT NULL AUTO_INCREMENT,
  `DatasetName` varchar(255) DEFAULT NULL,
  `GeoSeries` varchar(30) DEFAULT NULL,
  `PublicationTitle` longtext DEFAULT NULL,
  `Summary` longtext DEFAULT NULL,
  `ExperimentDesign` longtext DEFAULT NULL,
  `AboutCases` longtext DEFAULT NULL,
  `AboutTissue` longtext DEFAULT NULL,
  `AboutPlatform` longtext DEFAULT NULL,
  `AboutDataProcessing` longtext DEFAULT NULL,
  `Contributors` longtext DEFAULT NULL,
  `Citation` longtext DEFAULT NULL,
  `Acknowledgment` longtext DEFAULT NULL,
  `Notes` longtext DEFAULT NULL,
  `InvestigatorId` int(5) NOT NULL,
  `DatasetStatusId` int(5) NOT NULL,
  PRIMARY KEY (`DatasetId`),
  UNIQUE KEY `DatasetId` (`DatasetId`)
) ENGINE=MyISAM AUTO_INCREMENT=301 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Docs`
--

DROP TABLE IF EXISTS `Docs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Docs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `entry` varchar(255) NOT NULL,
  `title` varchar(255) NOT NULL,
  `content` text NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=10 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `EnsemblChip`
--

DROP TABLE IF EXISTS `EnsemblChip`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `EnsemblChip` (
  `Id` int(11) NOT NULL,
  `ProbeSetSize` int(11) NOT NULL,
  `Name` varchar(40) NOT NULL,
  `Type` enum('AFFY','OLIGO') DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `EnsemblProbe`
--

DROP TABLE IF EXISTS `EnsemblProbe`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `EnsemblProbe` (
  `Id` int(11) NOT NULL,
  `ChipId` int(11) NOT NULL,
  `ProbeSet` varchar(40) DEFAULT NULL,
  `Name` varchar(40) DEFAULT NULL,
  `length` int(11) NOT NULL,
  KEY `EnsemblProbeId` (`Id`),
  KEY `EnsemblProbeName` (`Name`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `EnsemblProbeLocation`
--

DROP TABLE IF EXISTS `EnsemblProbeLocation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `EnsemblProbeLocation` (
  `Chr` char(2) NOT NULL,
  `Start` int(11) NOT NULL,
  `Start_2016` int(11) DEFAULT NULL,
  `End` int(11) NOT NULL,
  `End_2016` int(11) DEFAULT NULL,
  `Strand` int(11) NOT NULL,
  `MisMataches` int(11) DEFAULT NULL,
  `ProbeId` int(11) NOT NULL,
  KEY `EnsemblLocationProbeId` (`ProbeId`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `GORef`
--

DROP TABLE IF EXISTS `GORef`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `GORef` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `goterm` varchar(255) DEFAULT NULL,
  `genes` text DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=17510 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Genbank`
--

DROP TABLE IF EXISTS `Genbank`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Genbank` (
  `Id` varchar(20) NOT NULL DEFAULT '',
  `Sequence` text DEFAULT NULL,
  `SpeciesId` smallint(5) unsigned NOT NULL DEFAULT 0,
  PRIMARY KEY (`Id`),
  FOREIGN KEY (SpeciesId) REFERENCES Species(SpeciesId),
  KEY `Id` (`Id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `GeneCategory`
--

DROP TABLE IF EXISTS `GeneCategory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `GeneCategory` (
  `Id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `Name` char(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`Id`),
  KEY `name_idx` (`Name`)
) ENGINE=MyISAM AUTO_INCREMENT=22 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `GeneChip`
--

DROP TABLE IF EXISTS `GeneChip`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `GeneChip` (
  `Id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `GeneChipId` int(5) DEFAULT NULL,
  `GeneChipName` varchar(200) DEFAULT NULL,
  `Name` char(30) NOT NULL DEFAULT '',
  `GeoPlatform` char(15) DEFAULT NULL,
  `Title` varchar(100) DEFAULT NULL,
  `SpeciesId` int(5) DEFAULT 1,
  `GO_tree_value` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`Id`),
  FOREIGN KEY (SpeciesId) REFERENCES Species(SpeciesId)
) ENGINE=MyISAM AUTO_INCREMENT=67 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `GeneChipEnsemblXRef`
--

DROP TABLE IF EXISTS `GeneChipEnsemblXRef`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `GeneChipEnsemblXRef` (
  `GeneChipId` int(11) NOT NULL,
  `EnsemblChipId` int(11) NOT NULL,
  FOREIGN KEY (GeneChipId) REFERENCES GeneChip(GeneChipId),
  FOREIGN KEY (EnsemblChipId) REFERENCES EnsemblChip(Id)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `GeneIDXRef`
--

DROP TABLE IF EXISTS `GeneIDXRef`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `GeneIDXRef` (
  `mouse` int(11) NOT NULL DEFAULT 0,
  `rat` int(11) NOT NULL DEFAULT 0,
  `human` int(11) NOT NULL DEFAULT 0,
  KEY `mouse_index` (`mouse`),
  KEY `rat_index` (`rat`),
  KEY `human_index` (`human`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `GeneList`
--

DROP TABLE IF EXISTS `GeneList`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `GeneList` (
  `SpeciesId` int(5) unsigned NOT NULL DEFAULT 1,
  `Id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `GeneSymbol` varchar(15) DEFAULT NULL,
  `GeneDescription` text DEFAULT NULL,
  `Chromosome` varchar(10) DEFAULT NULL,
  `TxStart` double DEFAULT NULL,
  `TxStart_2016` double DEFAULT NULL,
  `TxEnd` double DEFAULT NULL,
  `TxEnd_2016` double DEFAULT NULL,
  `Strand` char(1) DEFAULT NULL,
  `GeneID` varchar(10) DEFAULT NULL,
  `NM_ID` varchar(15) DEFAULT NULL,
  `kgID` varchar(10) DEFAULT NULL,
  `GenBankID` varchar(15) DEFAULT NULL,
  `UnigenID` varchar(15) DEFAULT NULL,
  `ProteinID` varchar(15) DEFAULT NULL,
  `AlignID` varchar(10) DEFAULT NULL,
  `exonCount` int(7) NOT NULL DEFAULT 0,
  `exonStarts` text DEFAULT NULL,
  `exonEnds` text DEFAULT NULL,
  `cdsStart` double DEFAULT NULL,
  `cdsStart_2016` double DEFAULT NULL,
  `cdsEnd` double DEFAULT NULL,
  `cdsEnd_2016` double DEFAULT NULL,
  `TxStart_mm8` double DEFAULT NULL,
  `TxEnd_mm8` double DEFAULT NULL,
  `Strand_mm8` char(1) DEFAULT NULL,
  `exonCount_mm8` int(7) DEFAULT NULL,
  `exonStarts_mm8` text DEFAULT NULL,
  `exonEnds_mm8` text DEFAULT NULL,
  `cdsStart_mm8` double DEFAULT NULL,
  `cdsEnd_mm8` double DEFAULT NULL,
  `Chromosome_mm8` varchar(10) DEFAULT NULL,
  `Info_mm9` text DEFAULT NULL,
  `RGD_ID` int(10) DEFAULT NULL,
  UNIQUE KEY `geneId` (`SpeciesId`,`Id`),
  FOREIGN KEY (SpeciesId) REFERENCES Species(SpeciesId),
  FOREIGN KEY (GenBankID) REFERENCES Genbank(Id),
  KEY `geneSymbol` (`GeneSymbol`),
  KEY `geneSymbol2` (`SpeciesId`,`GeneSymbol`),
  KEY `Loc1` (`SpeciesId`,`Chromosome`,`TxStart`),
  KEY `Loc2` (`SpeciesId`,`Chromosome`,`TxEnd`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `GeneList_rn3`
--

DROP TABLE IF EXISTS `GeneList_rn3`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `GeneList_rn3` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `ProbeSet` varchar(16) DEFAULT NULL,
  `geneSymbol` varchar(15) DEFAULT NULL,
  `geneID` varchar(10) DEFAULT NULL,
  `kgID` varchar(10) DEFAULT NULL,
  `geneDescription` text DEFAULT NULL,
  `genBankID` varchar(15) DEFAULT NULL,
  `unigenID` varchar(15) DEFAULT NULL,
  `score` int(4) DEFAULT NULL,
  `qStart` int(3) DEFAULT NULL,
  `qEnd` int(3) DEFAULT NULL,
  `qSize` int(3) DEFAULT NULL,
  `identity` varchar(7) DEFAULT NULL,
  `chromosome` varchar(8) DEFAULT NULL,
  `strand` char(1) DEFAULT NULL,
  `txStart` double DEFAULT NULL,
  `txEnd` double DEFAULT NULL,
  `txSize` double DEFAULT NULL,
  `span` int(7) DEFAULT NULL,
  `specificity` double DEFAULT NULL,
  `sequence` text DEFAULT NULL,
  `flag` int(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `geneSymbol` (`geneSymbol`),
  KEY `Loc1` (`chromosome`,`txStart`),
  KEY `Loc2` (`chromosome`,`txEnd`)
) ENGINE=MyISAM AUTO_INCREMENT=14917 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `GeneList_rn33`
--

DROP TABLE IF EXISTS `GeneList_rn33`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `GeneList_rn33` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `geneSymbol` varchar(15) DEFAULT NULL,
  `txStart` double DEFAULT NULL,
  `txEnd` double DEFAULT NULL,
  `exonCount` int(7) DEFAULT NULL,
  `NM_ID` varchar(15) DEFAULT NULL,
  `chromosome` varchar(8) DEFAULT NULL,
  `strand` char(1) DEFAULT NULL,
  `cdsStart` double DEFAULT NULL,
  `cdsEnd` double DEFAULT NULL,
  `exonStarts` text DEFAULT NULL,
  `exonEnds` text DEFAULT NULL,
  `kgID` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `geneSymbol` (`geneSymbol`),
  KEY `Loc1` (`chromosome`,`txStart`),
  KEY `Loc2` (`chromosome`,`txEnd`)
) ENGINE=MyISAM AUTO_INCREMENT=9790 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `GeneMap_cuiyan`
--

DROP TABLE IF EXISTS `GeneMap_cuiyan`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `GeneMap_cuiyan` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `TranscriptID` varchar(255) DEFAULT NULL,
  `GeneID` varchar(255) DEFAULT NULL,
  `Symbol` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=10537 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `GeneRIF`
--

DROP TABLE IF EXISTS `GeneRIF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `GeneRIF` (
  `Id` int(10) unsigned NOT NULL DEFAULT 0,
  `versionId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `symbol` varchar(30) NOT NULL DEFAULT '',
  `PubMed_ID` varchar(255) DEFAULT NULL,
  `SpeciesId` smallint(5) unsigned NOT NULL DEFAULT 1,
  `comment` text DEFAULT NULL,
  `email` varchar(50) DEFAULT NULL,
  `createtime` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `user_ip` varchar(20) DEFAULT NULL,
  `weburl` varchar(255) DEFAULT NULL,
  `initial` varchar(10) DEFAULT NULL,
  `display` tinyint(4) DEFAULT 1,
  `reason` varchar(100) NOT NULL DEFAULT '',
  PRIMARY KEY (`Id`,`versionId`),
  FOREIGN KEY (SpeciesId) REFERENCES Species(SpeciesId),
  KEY `name_idx` (`symbol`),
  KEY `status` (`display`),
  KEY `timestamp` (`createtime`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `GeneRIFXRef`
--

DROP TABLE IF EXISTS `GeneRIFXRef`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `GeneRIFXRef` (
  `GeneRIFId` int(10) unsigned NOT NULL DEFAULT 0,
  `versionId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `GeneCategoryId` smallint(5) unsigned NOT NULL DEFAULT 0,
  PRIMARY KEY (`GeneRIFId`,`versionId`,`GeneCategoryId`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `GeneRIF_BASIC`
--

DROP TABLE IF EXISTS `GeneRIF_BASIC`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `GeneRIF_BASIC` (
  `SpeciesId` smallint(5) unsigned NOT NULL DEFAULT 1,
  `GeneId` int(10) unsigned NOT NULL DEFAULT 0,
  `symbol` varchar(255) NOT NULL DEFAULT '',
  `PubMed_ID` int(10) unsigned NOT NULL DEFAULT 0,
  `createtime` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `comment` text DEFAULT NULL,
  `VersionId` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`GeneId`,`SpeciesId`,`createtime`,`PubMed_ID`,`VersionId`),
  FOREIGN KEY (SpeciesId) REFERENCES Species(SpeciesId),
  KEY `symbol` (`symbol`,`SpeciesId`,`createtime`),
  FULLTEXT KEY `commts` (`comment`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Geno`
--

DROP TABLE IF EXISTS `Geno`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Geno` (
  `Id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `SpeciesId` smallint(5) unsigned NOT NULL DEFAULT 1,
  `Name` varchar(40) NOT NULL DEFAULT '',
  `Marker_Name` varchar(40) DEFAULT NULL,
  `Chr` char(3) DEFAULT NULL,
  `Mb` double DEFAULT NULL,
  `Mb_2016` double DEFAULT NULL,
  `Sequence` text DEFAULT NULL,
  `Source` varchar(40) DEFAULT NULL,
  `chr_num` smallint(5) unsigned DEFAULT NULL,
  `Source2` varchar(40) DEFAULT NULL,
  `Comments` varchar(255) DEFAULT NULL,
  `used_by_geno_file` varchar(40) DEFAULT NULL,
  `Mb_mm8` double DEFAULT NULL,
  `Chr_mm8` char(3) DEFAULT NULL,
  PRIMARY KEY (`Id`),
  UNIQUE KEY `species_name` (`SpeciesId`,`Name`),
  FOREIGN KEY (SpeciesId) REFERENCES Species(SpeciesId),
  KEY `Name` (`Name`)
) ENGINE=MyISAM AUTO_INCREMENT=716770 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `GenoCode`
--

DROP TABLE IF EXISTS `GenoCode`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `GenoCode` (
  `InbredSetId` smallint(5) unsigned NOT NULL DEFAULT 1,
  `AlleleType` char(3) NOT NULL DEFAULT '',
  `AlleleSymbol` char(2) NOT NULL DEFAULT '',
  `DatabaseValue` smallint(5) DEFAULT NULL,
  PRIMARY KEY (`InbredSetId`,`AlleleType`,`AlleleSymbol`),
  UNIQUE KEY `InbredSetId_AlleleType` (`InbredSetId`,`AlleleType`),
  UNIQUE KEY `InbredSetId_AlleleSymbol` (`InbredSetId`,`AlleleSymbol`),
  UNIQUE KEY `InbredSetId_DatabaseValue` (`InbredSetId`,`DatabaseValue`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `GenoData`
--

DROP TABLE IF EXISTS `GenoData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `GenoData` (
  `Id` int(10) unsigned NOT NULL DEFAULT 0,
  `StrainId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `value` float NOT NULL,
  UNIQUE KEY `DataId` (`Id`,`StrainId`),
  FOREIGN KEY (StrainId) REFERENCES Strain(Id)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `GenoFile`
--

DROP TABLE IF EXISTS `GenoFile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `GenoFile` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `server` varchar(100) NOT NULL,
  `InbredSetID` int(11) NOT NULL,
  `location` varchar(255) NOT NULL,
  `title` varchar(255) NOT NULL,
  `sort` int(3) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `GenoFreeze`
--

DROP TABLE IF EXISTS `GenoFreeze`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `GenoFreeze` (
  `Id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `Name` varchar(100) NOT NULL DEFAULT '',
  `FullName` varchar(100) NOT NULL DEFAULT '',
  `ShortName` varchar(100) NOT NULL DEFAULT '',
  `CreateTime` date NOT NULL DEFAULT '2001-01-01',
  `public` tinyint(4) NOT NULL DEFAULT 0,
  `InbredSetId` smallint(5) unsigned DEFAULT 1,
  `confidentiality` tinyint(3) unsigned DEFAULT 0,
  `AuthorisedUsers` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`Id`),
  FOREIGN KEY (InbredSetId) REFERENCES InbredSet(InbredSetId),
) ENGINE=MyISAM AUTO_INCREMENT=37 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `GenoSE`
--

DROP TABLE IF EXISTS `GenoSE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `GenoSE` (
  `DataId` int(10) unsigned NOT NULL DEFAULT 0,
  `StrainId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `error` float NOT NULL,
  UNIQUE KEY `DataId` (`DataId`,`StrainId`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `GenoXRef`
--

DROP TABLE IF EXISTS `GenoXRef`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `GenoXRef` (
  `GenoFreezeId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `GenoId` int(10) unsigned NOT NULL DEFAULT 0,
  `DataId` int(10) unsigned NOT NULL DEFAULT 0,
  `cM` double DEFAULT 0,
  `Used_for_mapping` char(1) DEFAULT 'N',
  UNIQUE KEY `ProbeSetId` (`GenoFreezeId`,`GenoId`),
  UNIQUE KEY `DataId` (`DataId`),
  FOREIGN KEY (GenoFreezeId) REFERENCES GenoFreeze(Id),
  FOREIGN KEY (GenoId) REFERENCES Geno(Id),
  KEY `GenoId` (`GenoId`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `H2`
--

DROP TABLE IF EXISTS `H2`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `H2` (
  `DataId` int(10) unsigned NOT NULL DEFAULT 0,
  `ICH2` double NOT NULL DEFAULT 0,
  `H2SE` double NOT NULL DEFAULT 0,
  `HPH2` double NOT NULL DEFAULT 0,
  UNIQUE KEY `DataId` (`DataId`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Homologene`
--

DROP TABLE IF EXISTS `Homologene`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Homologene` (
  `HomologeneId` int(11) DEFAULT NULL,
  `GeneId` int(11) DEFAULT NULL,
  `TaxonomyId` int(11) DEFAULT NULL,
  KEY `GeneId` (`GeneId`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `InbredSet`
--

DROP TABLE IF EXISTS `InbredSet`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `InbredSet` (
  `Id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `InbredSetId` int(5) DEFAULT NULL,
  `InbredSetName` varchar(100) DEFAULT NULL,
  `Name` char(30) NOT NULL DEFAULT '',
  `SpeciesId` smallint(5) unsigned DEFAULT 1,
  `FullName` varchar(100) DEFAULT NULL,
  `public` tinyint(3) unsigned DEFAULT 2,
  `MappingMethodId` char(50) DEFAULT '1',
  `GeneticType` varchar(255) DEFAULT NULL,
  `Family` varchar(100) DEFAULT NULL,
  `FamilyOrder` int(5) DEFAULT NULL,
  `MenuOrderId` double NOT NULL,
  `InbredSetCode` varchar(5) DEFAULT NULL,
  PRIMARY KEY (`Id`),
  FOREIGN KEY (SpeciesId) REFERENCES Species(SpeciesId),
  FOREIGN KEY (MappingMethodId) REFERENCES MappingMethod(Id),
  KEY `Name` (`Name`),
  KEY `SpeciesId` (`SpeciesId`),
  KEY `Id` (`Id`),
  KEY `InbredSetCode` (`InbredSetCode`)
) ENGINE=MyISAM AUTO_INCREMENT=83 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `IndelAll`
--

DROP TABLE IF EXISTS `IndelAll`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `IndelAll` (
  `Id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `SpeciesId` smallint(5) unsigned DEFAULT 1,
  `SourceId` smallint(5) unsigned DEFAULT NULL,
  `Name` char(30) DEFAULT NULL,
  `Chromosome` char(2) DEFAULT NULL,
  `Mb_start` double DEFAULT NULL,
  `Mb_start_2016` double DEFAULT NULL,
  `Strand` char(1) DEFAULT NULL,
  `Type` char(15) DEFAULT NULL,
  `Mb_end` double DEFAULT NULL,
  `Mb_end_2016` double DEFAULT NULL,
  `Size` double DEFAULT NULL,
  `InDelSequence` char(30) DEFAULT NULL,
  PRIMARY KEY (`Id`),
  UNIQUE KEY `SnpId` (`SpeciesId`,`Name`),
  FOREIGN KEY (SpeciesId) REFERENCES Species(SpeciesId),
  KEY `SnpId2` (`Name`),
  KEY `Position` (`SpeciesId`,`Chromosome`,`Mb_start`) USING BTREE
) ENGINE=MyISAM AUTO_INCREMENT=142895 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `IndelXRef`
--

DROP TABLE IF EXISTS `IndelXRef`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `IndelXRef` (
  `IndelId` int(10) unsigned NOT NULL DEFAULT 0,
  `StrainId1` smallint(5) unsigned NOT NULL DEFAULT 0,
  `StrainId2` smallint(5) unsigned DEFAULT NULL,
  PRIMARY KEY (`IndelId`,`StrainId1`),
  FOREIGN KEY (IndelId) REFERENCES IndelAll(Id),
  FOREIGN KEY (StrainId1) REFERENCES Strain(Id),
  FOREIGN KEY (StrainId2) REFERENCES Strain(Id)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `InfoFiles`
--

DROP TABLE IF EXISTS `InfoFiles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `InfoFiles` (
  `DatasetId` int(5) DEFAULT NULL,
  `SpeciesId` int(5) DEFAULT NULL,
  `TissueId` int(5) DEFAULT NULL,
  `InbredSetId` int(5) DEFAULT NULL,
  `GeneChipId` int(5) DEFAULT NULL,
  `AvgMethodId` int(5) DEFAULT NULL,
  `InfoFileTitle` longtext DEFAULT NULL,
  `Specifics` longtext DEFAULT NULL,
  `Status` varchar(255) DEFAULT NULL,
  `Title` varchar(255) DEFAULT NULL,
  `Organism` varchar(255) DEFAULT NULL,
  `Experiment_Type` longtext DEFAULT NULL,
  `Summary` longtext DEFAULT NULL,
  `Overall_Design` longtext DEFAULT NULL,
  `Contributor` longtext DEFAULT NULL,
  `Citation` longtext DEFAULT NULL,
  `Submission_Date` varchar(255) DEFAULT NULL,
  `Contact_Name` varchar(255) DEFAULT NULL,
  `Emails` varchar(255) DEFAULT NULL,
  `Phone` varchar(255) DEFAULT NULL,
  `URL` varchar(255) DEFAULT NULL,
  `Organization_Name` varchar(255) DEFAULT NULL,
  `Department` varchar(255) DEFAULT NULL,
  `Laboratory` varchar(255) DEFAULT NULL,
  `Street` varchar(255) DEFAULT NULL,
  `City` varchar(255) DEFAULT NULL,
  `State` varchar(255) DEFAULT NULL,
  `ZIP` varchar(255) DEFAULT NULL,
  `Country` varchar(255) DEFAULT NULL,
  `Platforms` varchar(255) DEFAULT NULL,
  `Samples` longtext DEFAULT NULL,
  `Species` varchar(255) DEFAULT NULL,
  `Normalization` varchar(255) DEFAULT NULL,
  `InbredSet` varchar(255) DEFAULT NULL,
  `InfoPageName` varchar(255) NOT NULL,
  `DB_Name` varchar(255) DEFAULT NULL,
  `Organism_Id` varchar(60) DEFAULT NULL,
  `InfoPageTitle` varchar(255) DEFAULT NULL,
  `GN_AccesionId` int(4) DEFAULT NULL,
  `Tissue` varchar(60) DEFAULT NULL,
  `AuthorizedUsers` varchar(100) DEFAULT NULL,
  `About_Cases` longtext DEFAULT NULL,
  `About_Tissue` longtext DEFAULT NULL,
  `About_Download` longtext DEFAULT NULL,
  `About_Array_Platform` longtext DEFAULT NULL,
  `About_Data_Values_Processing` longtext DEFAULT NULL,
  `Data_Source_Acknowledge` longtext DEFAULT NULL,
  `Progreso` varchar(20) DEFAULT NULL,
  `QualityControlStatus` longtext DEFAULT NULL,
  `InfoFileId` int(6) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`InfoFileId`),
  UNIQUE KEY `InfoPageName` (`InfoPageName`),
  UNIQUE KEY `GN_AccesionId` (`GN_AccesionId`)
) ENGINE=MyISAM AUTO_INCREMENT=1470 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `InfoFilesUser_md5`
--

DROP TABLE IF EXISTS `InfoFilesUser_md5`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `InfoFilesUser_md5` (
  `Username` varchar(16) DEFAULT NULL,
  `Password` varchar(32) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Investigators`
--

DROP TABLE IF EXISTS `Investigators`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Investigators` (
  `FirstName` varchar(20) DEFAULT NULL,
  `LastName` varchar(20) DEFAULT NULL,
  `Address` varchar(200) DEFAULT NULL,
  `City` varchar(20) DEFAULT NULL,
  `State` varchar(20) DEFAULT NULL,
  `ZipCode` varchar(20) DEFAULT NULL,
  `Phone` varchar(200) DEFAULT NULL,
  `Email` varchar(200) DEFAULT NULL,
  `Country` varchar(35) DEFAULT NULL,
  `Url` text DEFAULT NULL,
  `UserName` varchar(30) DEFAULT NULL,
  `UserPass` varchar(50) DEFAULT NULL,
  `UserDate` datetime DEFAULT NULL,
  `UserLevel` int(8) DEFAULT NULL,
  `OrganizationId` int(5) NOT NULL,
  `InvestigatorId` int(5) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`InvestigatorId`),
  FOREIGN KEY (OrganizationId) REFERENCES Organizations(OrganizationId)
) ENGINE=MyISAM AUTO_INCREMENT=151 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `LCorrRamin3`
--

DROP TABLE IF EXISTS `LCorrRamin3`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `LCorrRamin3` (
  `GeneId1` int(12) unsigned DEFAULT NULL,
  `GeneId2` int(12) unsigned DEFAULT NULL,
  `value` double DEFAULT NULL,
  KEY `GeneId1` (`GeneId1`),
  KEY `GeneId2` (`GeneId2`),
  KEY `GeneId1_2` (`GeneId1`,`GeneId2`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `MachineAccessLog`
--

DROP TABLE IF EXISTS `MachineAccessLog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MachineAccessLog` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `accesstime` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `ip_address` char(20) NOT NULL DEFAULT '0.0.0.0',
  `db_id` tinyint(3) unsigned NOT NULL DEFAULT 0,
  `data_id` int(10) unsigned DEFAULT NULL,
  `action` char(10) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=514946 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `MappingMethod`
--

DROP TABLE IF EXISTS `MappingMethod`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MappingMethod` (
  `Id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `Name` varchar(100) NOT NULL DEFAULT '',
  PRIMARY KEY (`Id`)
) ENGINE=MyISAM AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `NStrain`
--

DROP TABLE IF EXISTS `NStrain`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `NStrain` (
  `DataId` int(10) unsigned DEFAULT NULL,
  `StrainId` smallint(5) unsigned DEFAULT NULL,
  `count` varchar(5) DEFAULT NULL,
  UNIQUE KEY `DataId` (`DataId`,`StrainId`),
  FOREIGN KEY (StrainId) REFERENCES Strain(Id)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `News`
--

DROP TABLE IF EXISTS `News`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `News` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `date` date DEFAULT NULL,
  `details` text DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=296 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Organizations`
--

DROP TABLE IF EXISTS `Organizations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Organizations` (
  `OrganizationId` int(5) NOT NULL AUTO_INCREMENT,
  `OrganizationName` varchar(200) NOT NULL,
  PRIMARY KEY (`OrganizationId`),
  UNIQUE KEY `OrganizationId` (`OrganizationId`),
  UNIQUE KEY `OrganizationName` (`OrganizationName`)
) ENGINE=MyISAM AUTO_INCREMENT=92 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Phenotype`
--

DROP TABLE IF EXISTS `Phenotype`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Phenotype` (
  `Id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `Pre_publication_description` text DEFAULT NULL,
  `Post_publication_description` text DEFAULT NULL,
  `Original_description` text DEFAULT NULL,
  `Units` varchar(100) NOT NULL DEFAULT 'Unknown',
  `Pre_publication_abbreviation` varchar(40) DEFAULT NULL,
  `Post_publication_abbreviation` varchar(40) DEFAULT NULL,
  `Lab_code` varchar(255) DEFAULT NULL,
  `Submitter` varchar(255) DEFAULT NULL,
  `Owner` varchar(255) DEFAULT NULL,
  `Authorized_Users` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`Id`),
  KEY `Post_publication_description_Index` (`Post_publication_description`(255)),
  KEY `Pre_publication_description_Index` (`Pre_publication_description`(255)),
  KEY `Pre_publication_abbreviation_Index` (`Pre_publication_abbreviation`),
  KEY `Post_publication_abbreviation_Index` (`Post_publication_abbreviation`),
  KEY `Lab_code` (`Lab_code`),
  FULLTEXT KEY `Post_publication_description` (`Post_publication_description`),
  FULLTEXT KEY `Pre_publication_description` (`Pre_publication_description`),
  FULLTEXT KEY `Pre_publication_abbreviation` (`Pre_publication_abbreviation`),
  FULLTEXT KEY `Post_publication_abbreviation` (`Post_publication_abbreviation`),
  FULLTEXT KEY `Lab_code1` (`Lab_code`),
  FULLTEXT KEY `SEARCH_FULL_IDX` (`Post_publication_description`,`Pre_publication_description`,`Pre_publication_abbreviation`,`Post_publication_abbreviation`,`Lab_code`)
) ENGINE=MyISAM AUTO_INCREMENT=29299 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Probe`
--

DROP TABLE IF EXISTS `Probe`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Probe` (
  `Id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `ProbeSetId` int(10) unsigned NOT NULL DEFAULT 0,
  `Name` char(20) DEFAULT NULL,
  `Sequence` char(30) DEFAULT NULL,
  `ExonNo` char(7) DEFAULT NULL,
  `SerialOrder` double DEFAULT NULL,
  `Tm` double DEFAULT NULL,
  `E_GSB` double DEFAULT NULL,
  `E_NSB` double DEFAULT NULL,
  PRIMARY KEY (`Id`),
  UNIQUE KEY `ProbeSetId` (`ProbeSetId`,`Name`),
  FOREIGN KEY (ProbeSetId) REFERENCES ProbeSet(ProbeSetId),
  KEY `SerialOrder` (`ProbeSetId`,`SerialOrder`)
) ENGINE=MyISAM AUTO_INCREMENT=19054073 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ProbeData`
--

DROP TABLE IF EXISTS `ProbeData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ProbeData` (
  `Id` int(10) unsigned NOT NULL DEFAULT 0,
  `StrainId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `value` float NOT NULL,
  UNIQUE KEY `DataId` (`Id`,`StrainId`),
  FOREIGN KEY (StrainId) REFERENCES Strain(Id)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ProbeFreeze`
--

DROP TABLE IF EXISTS `ProbeFreeze`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ProbeFreeze` (
  `Id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `ProbeFreezeId` int(5) DEFAULT NULL,
  `ChipId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `TissueId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `Name` varchar(100) NOT NULL DEFAULT '',
  `FullName` varchar(100) NOT NULL DEFAULT '',
  `ShortName` varchar(100) NOT NULL DEFAULT '',
  `CreateTime` date NOT NULL DEFAULT '0000-00-00',
  `InbredSetId` smallint(5) unsigned DEFAULT 1,
  PRIMARY KEY (`Id`),
  UNIQUE KEY `Name` (`Name`),
  FOREIGN KEY (TissueId) REFERENCES Tissue(TissueId),
  KEY `TissueId` (`TissueId`),
  KEY `InbredSetId` (`InbredSetId`)
) ENGINE=MyISAM AUTO_INCREMENT=416 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ProbeH2`
--

DROP TABLE IF EXISTS `ProbeH2`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ProbeH2` (
  `ProbeFreezeId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `ProbeId` int(10) unsigned NOT NULL DEFAULT 0,
  `h2` double DEFAULT NULL,
  `weight` double DEFAULT NULL,
  UNIQUE KEY `ProbeId` (`ProbeFreezeId`,`ProbeId`),
  FOREIGN KEY (ProbeFreezeId) REFERENCES ProbeFreeze(ProbeFreezeId),
  FOREIGN KEY (ProbeId) REFERENCES Probe(Id)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ProbeSE`
--

DROP TABLE IF EXISTS `ProbeSE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ProbeSE` (
  `DataId` int(10) unsigned NOT NULL DEFAULT 0,
  `StrainId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `error` float NOT NULL,
  UNIQUE KEY `DataId` (`DataId`,`StrainId`),
  FOREIGN KEY (StrainId) REFERENCES Strain(Id)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ProbeSet`
--

DROP TABLE IF EXISTS `ProbeSet`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ProbeSet` (
  `Id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `ChipId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `Name` varchar(100) DEFAULT NULL,
  `TargetId` varchar(150) DEFAULT NULL,
  `Symbol` varchar(100) DEFAULT NULL,
  `description` longtext DEFAULT NULL,
  `Chr` char(3) DEFAULT NULL,
  `Mb` double DEFAULT NULL,
  `Chr_2016` char(3) DEFAULT NULL,
  `Mb_2016` double DEFAULT NULL,
  `alias` longtext DEFAULT NULL,
  `GeneId` varchar(20) DEFAULT NULL,
  `GenbankId` varchar(1000) DEFAULT NULL,
  `SNP` int(2) DEFAULT NULL,
  `BlatSeq` text NOT NULL,
  `TargetSeq` text DEFAULT NULL,
  `UniGeneId` varchar(100) DEFAULT NULL,
  `Strand_Probe` char(1) DEFAULT NULL,
  `Strand_Gene` char(1) DEFAULT NULL,
  `OMIM` varchar(20) DEFAULT NULL,
  `comments` text NOT NULL,
  `Probe_set_target_region` varchar(255) DEFAULT NULL,
  `Probe_set_specificity` double DEFAULT NULL,
  `Probe_set_BLAT_score` double DEFAULT NULL,
  `Probe_set_Blat_Mb_start` double DEFAULT NULL,
  `Probe_set_Blat_Mb_end` double DEFAULT NULL,
  `Probe_set_Blat_Mb_start_2016` double DEFAULT NULL,
  `Probe_set_Blat_Mb_end_2016` double DEFAULT NULL,
  `Probe_set_strand` varchar(255) DEFAULT NULL,
  `Probe_set_Note_by_RW` varchar(255) DEFAULT NULL,
  `flag` char(1) DEFAULT NULL,
  `Symbol_H` varchar(100) DEFAULT NULL,
  `description_H` varchar(255) DEFAULT NULL,
  `chromosome_H` char(3) DEFAULT NULL,
  `MB_H` double DEFAULT NULL,
  `alias_H` varchar(255) DEFAULT NULL,
  `GeneId_H` varchar(20) DEFAULT NULL,
  `chr_num` smallint(5) unsigned DEFAULT 30,
  `name_num` int(10) unsigned DEFAULT 4294967290,
  `Probe_Target_Description` varchar(225) DEFAULT NULL,
  `RefSeq_TranscriptId` varchar(255) DEFAULT NULL,
  `ENSEMBLGeneId` varchar(50) DEFAULT NULL,
  `Chr_mm8` char(3) DEFAULT NULL,
  `Mb_mm8` double DEFAULT NULL,
  `Probe_set_Blat_Mb_start_mm8` double DEFAULT NULL,
  `Probe_set_Blat_Mb_end_mm8` double DEFAULT NULL,
  `HomoloGeneID` varchar(20) DEFAULT NULL,
  `Biotype_ENS` varchar(255) DEFAULT NULL,
  `ProteinID` varchar(50) DEFAULT NULL,
  `ProteinName` varchar(50) DEFAULT NULL,
  `UniProtID` varchar(20) DEFAULT NULL,
  `Flybase_Id` varchar(25) DEFAULT NULL,
  `RGD_ID` int(10) DEFAULT NULL,
  `HMDB_ID` varchar(255) DEFAULT NULL,
  `Confidence` int(5) DEFAULT NULL,
  `ChEBI_ID` int(10) DEFAULT NULL,
  `ChEMBL_ID` varchar(100) DEFAULT NULL,
  `CAS_number` varchar(100) DEFAULT NULL,
  `PubChem_ID` int(10) DEFAULT NULL,
  `ChemSpider_ID` int(10) DEFAULT NULL,
  `UNII_ID` varchar(100) DEFAULT NULL,
  `EC_number` varchar(100) DEFAULT NULL,
  `KEGG_ID` varchar(100) DEFAULT NULL,
  `Molecular_Weight` double DEFAULT NULL,
  `Nugowiki_ID` int(10) DEFAULT NULL,
  `Type` varchar(255) DEFAULT NULL,
  `Tissue` varchar(255) DEFAULT NULL,
  `PrimaryName` varchar(255) DEFAULT NULL,
  `SecondaryNames` longtext DEFAULT NULL,
  `PeptideSequence` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`Id`),
  UNIQUE KEY `ProbeSetId` (`ChipId`,`Name`),
  FOREIGN KEY (HomoloGeneID) REFERENCES Homologene(HomologeneId),
  KEY `Name_IDX` (`Name`),
  KEY `symbol_IDX` (`Symbol`),
  KEY `RefSeq_TranscriptId` (`RefSeq_TranscriptId`),
  KEY `GENBANK_IDX` (`GenbankId`),
  KEY `TargetId` (`TargetId`),
  KEY `Position` (`Chr`),
  KEY `GeneId_IDX` (`GeneId`),
  FULLTEXT KEY `SEARCH_GENE_IDX` (`Symbol`,`alias`),
  FULLTEXT KEY `SEARCH_FULL_IDX` (`Name`,`description`,`Symbol`,`alias`,`GenbankId`,`UniGeneId`,`Probe_Target_Description`),
  FULLTEXT KEY `RefSeq_FULL_IDX` (`RefSeq_TranscriptId`)
) ENGINE=MyISAM AUTO_INCREMENT=12118724 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ProbeSetData`
--

DROP TABLE IF EXISTS `ProbeSetData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ProbeSetData` (
  `Id` int(10) unsigned NOT NULL DEFAULT 0,
  `StrainId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `value` float NOT NULL,
  UNIQUE KEY `DataId` (`Id`,`StrainId`),
  FOREIGN KEY (StrainId) REFERENCES Strain(Id)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ProbeSetFreeze`
--

DROP TABLE IF EXISTS `ProbeSetFreeze`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ProbeSetFreeze` (
  `Id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `ProbeFreezeId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `AvgID` smallint(5) unsigned NOT NULL DEFAULT 0,
  `Name` varchar(40) DEFAULT NULL,
  `Name2` varchar(100) NOT NULL DEFAULT '',
  `FullName` varchar(100) NOT NULL DEFAULT '',
  `ShortName` varchar(100) NOT NULL DEFAULT '',
  `CreateTime` date NOT NULL DEFAULT '0000-00-00',
  `OrderList` int(5) DEFAULT NULL,
  `public` tinyint(4) NOT NULL DEFAULT 0,
  `confidentiality` tinyint(4) NOT NULL DEFAULT 0,
  `AuthorisedUsers` varchar(300) NOT NULL,
  `DataScale` varchar(20) NOT NULL DEFAULT 'log2',
  PRIMARY KEY (`Id`),
  UNIQUE KEY `FullName` (`FullName`),
  UNIQUE KEY `Name` (`Name`),
  FOREIGN KEY (ProbeFreezeId) REFERENCES ProbeFreeze(ProbeFreezeId),
  KEY `NameIndex` (`Name2`),
  KEY `ShortName` (`ShortName`),
  KEY `ProbeFreezeId` (`ProbeFreezeId`),
  KEY `conf_and_public` (`confidentiality`,`public`)
) ENGINE=MyISAM AUTO_INCREMENT=1006 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ProbeSetSE`
--

DROP TABLE IF EXISTS `ProbeSetSE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ProbeSetSE` (
  `DataId` int(10) unsigned NOT NULL DEFAULT 0,
  `StrainId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `error` float NOT NULL,
  UNIQUE KEY `DataId` (`DataId`,`StrainId`),
  FOREIGN KEY (StrainId) REFERENCES Strain(Id)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ProbeSetXRef`
--

DROP TABLE IF EXISTS `ProbeSetXRef`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ProbeSetXRef` (
  `ProbeSetFreezeId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `ProbeSetId` int(10) unsigned NOT NULL DEFAULT 0,
  `DataId` int(10) unsigned NOT NULL DEFAULT 0,
  `Locus_old` char(20) DEFAULT NULL,
  `LRS_old` double DEFAULT NULL,
  `pValue_old` double DEFAULT NULL,
  `mean` double DEFAULT NULL,
  `se` double DEFAULT NULL,
  `Locus` char(20) DEFAULT NULL,
  `LRS` double DEFAULT NULL,
  `pValue` double DEFAULT NULL,
  `additive` double DEFAULT NULL,
  `h2` float DEFAULT NULL,
  UNIQUE KEY `ProbeSetId` (`ProbeSetFreezeId`,`ProbeSetId`),
  UNIQUE KEY `DataId_IDX` (`DataId`),
  FOREIGN KEY (ProbeSetFreezeId) REFERENCES ProbeSetFreeze(Id),
  FOREIGN KEY (ProbeSetId) REFERENCES ProbeSet(Id),
  KEY `ProbeSetId1` (`ProbeSetId`),
  KEY `Locus` (`Locus`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ProbeXRef`
--

DROP TABLE IF EXISTS `ProbeXRef`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ProbeXRef` (
  `ProbeFreezeId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `ProbeId` int(10) unsigned NOT NULL DEFAULT 0,
  `DataId` int(10) unsigned NOT NULL DEFAULT 0,
  UNIQUE KEY `ProbeId` (`ProbeFreezeId`,`ProbeId`),
  UNIQUE KEY `DataId_IDX` (`DataId`),
  FOREIGN KEY (ProbeFreezeId) REFERENCES ProbeFreeze(ProbeFreezeId),
  FOREIGN KEY (ProbeId) REFERENCES Probe(Id)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Publication`
--

DROP TABLE IF EXISTS `Publication`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Publication` (
  `Id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `PubMed_ID` int(10) unsigned DEFAULT NULL,
  `Abstract` text DEFAULT NULL,
  `Authors` text NOT NULL,
  `Title` varchar(255) DEFAULT NULL,
  `Journal` varchar(255) DEFAULT NULL,
  `Volume` varchar(255) DEFAULT NULL,
  `Pages` varchar(255) DEFAULT NULL,
  `Month` varchar(255) DEFAULT NULL,
  `Year` varchar(255) NOT NULL DEFAULT '0',
  PRIMARY KEY (`Id`),
  UNIQUE KEY `Name` (`PubMed_ID`),
  KEY `PubMed_ID` (`PubMed_ID`),
  FULLTEXT KEY `Abstract1` (`Abstract`),
  FULLTEXT KEY `Title1` (`Title`),
  FULLTEXT KEY `Authors1` (`Authors`),
  FULLTEXT KEY `SEARCH_FULL_IDX` (`Abstract`,`Title`,`Authors`)
) ENGINE=MyISAM AUTO_INCREMENT=26076 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `PublishData`
--

DROP TABLE IF EXISTS `PublishData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `PublishData` (
  `Id` int(10) unsigned NOT NULL DEFAULT 0,
  `StrainId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `value` float(14,6) DEFAULT NULL,
  UNIQUE KEY `DataId` (`Id`,`StrainId`),
  FOREIGN KEY (StrainId) REFERENCES Strain(Id)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `PublishFreeze`
--

DROP TABLE IF EXISTS `PublishFreeze`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `PublishFreeze` (
  `Id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `Name` varchar(100) NOT NULL DEFAULT '',
  `FullName` varchar(100) NOT NULL DEFAULT '',
  `ShortName` varchar(100) NOT NULL DEFAULT '',
  `CreateTime` date NOT NULL DEFAULT '2001-01-01',
  `public` tinyint(4) NOT NULL DEFAULT 0,
  `InbredSetId` smallint(5) unsigned DEFAULT 1,
  `confidentiality` tinyint(3) DEFAULT 0,
  `AuthorisedUsers` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`Id`),
  FOREIGN KEY (InbredSetId) REFERENCES InbredSet(InbredSetId),
  KEY `InbredSetId` (`InbredSetId`)
) ENGINE=MyISAM AUTO_INCREMENT=60 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `PublishSE`
--

DROP TABLE IF EXISTS `PublishSE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `PublishSE` (
  `DataId` int(10) unsigned NOT NULL DEFAULT 0,
  `StrainId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `error` float NOT NULL,
  UNIQUE KEY `DataId` (`DataId`,`StrainId`),
  FOREIGN KEY (StrainId) REFERENCES Strain(Id)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `PublishXRef`
--

DROP TABLE IF EXISTS `PublishXRef`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `PublishXRef` (
  `Id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `InbredSetId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `PhenotypeId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `PublicationId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `DataId` int(10) unsigned NOT NULL DEFAULT 0,
  `mean` double DEFAULT NULL,
  `Locus` char(50) DEFAULT NULL,
  `LRS` double DEFAULT NULL,
  `additive` double DEFAULT NULL,
  `Sequence` smallint(5) unsigned NOT NULL DEFAULT 1,
  `comments` text NOT NULL,
  UNIQUE KEY `InbredSet` (`InbredSetId`,`Id`),
  UNIQUE KEY `record` (`InbredSetId`,`PhenotypeId`,`PublicationId`,`Sequence`),
  UNIQUE KEY `PhenotypeId` (`PhenotypeId`),
  UNIQUE KEY `DataId` (`DataId`),
  FOREIGN KEY (InbredSetId) REFERENCES InbredSet(InbredSetId),
  FOREIGN KEY (PhenotypeId) REFERENCES Phenotype(Id),
  FOREIGN KEY (PublicationId) REFERENCES Publication(Id),
  KEY `InbredSetId` (`InbredSetId`),
  KEY `Locus` (`Locus`),
  KEY `PublicationId` (`PublicationId`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `RatSnpPattern`
--

DROP TABLE IF EXISTS `RatSnpPattern`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RatSnpPattern` (
  `Id` int(12) NOT NULL AUTO_INCREMENT,
  `SnpId` int(12) NOT NULL,
  `BN` char(1) DEFAULT NULL,
  `F344` char(1) DEFAULT NULL,
  `ACI` char(1) DEFAULT NULL,
  `BBDP` char(1) DEFAULT NULL,
  `FHH` char(1) DEFAULT NULL,
  `FHL` char(1) DEFAULT NULL,
  `GK` char(1) DEFAULT NULL,
  `LE` char(1) DEFAULT NULL,
  `LEW` char(1) DEFAULT NULL,
  `LH` char(1) DEFAULT NULL,
  `LL` char(1) DEFAULT NULL,
  `LN` char(1) DEFAULT NULL,
  `MHS` char(1) DEFAULT NULL,
  `MNS` char(1) DEFAULT NULL,
  `SBH` char(1) DEFAULT NULL,
  `SBN` char(1) DEFAULT NULL,
  `SHR` char(1) DEFAULT NULL,
  `SHRSP` char(1) DEFAULT NULL,
  `SR` char(1) DEFAULT NULL,
  `SS` char(1) DEFAULT NULL,
  `WAG` char(1) DEFAULT NULL,
  `WLI` char(1) DEFAULT NULL,
  `WMI` char(1) DEFAULT NULL,
  `WKY` char(1) DEFAULT NULL,
  `ACI_N` char(1) DEFAULT NULL,
  `BN_N` char(1) DEFAULT NULL,
  `BUF_N` char(1) DEFAULT NULL,
  `F344_N` char(1) DEFAULT NULL,
  `M520_N` char(1) DEFAULT NULL,
  `MR_N` char(1) DEFAULT NULL,
  `WKY_N` char(1) DEFAULT NULL,
  `WN_N` char(1) DEFAULT NULL,
  PRIMARY KEY (`Id`),
  UNIQUE KEY `SnpId` (`SnpId`)
) ENGINE=MyISAM AUTO_INCREMENT=4711685 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Sample`
--

DROP TABLE IF EXISTS `Sample`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Sample` (
  `Id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `StrainId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `Name` varchar(30) DEFAULT NULL,
  `Age` smallint(6) NOT NULL DEFAULT 0,
  `Sex` enum('F','M') NOT NULL DEFAULT 'F',
  `CreateTime` date NOT NULL DEFAULT '2001-01-01',
  `TissueType` varchar(30) DEFAULT NULL,
  `FromSrc` varchar(10) DEFAULT NULL,
  `ImageURL` varchar(100) DEFAULT NULL,
  `CELURL` varchar(120) DEFAULT NULL,
  `DATURL` varchar(100) DEFAULT NULL,
  `CHPURL` varchar(100) DEFAULT NULL,
  `RPTURL` varchar(100) DEFAULT NULL,
  `EXPURL` varchar(100) DEFAULT NULL,
  `TXTURL` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`Id`),
  UNIQUE KEY `Name` (`StrainId`,`Name`,`CreateTime`)
) ENGINE=MyISAM AUTO_INCREMENT=252 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `SampleXRef`
--

DROP TABLE IF EXISTS `SampleXRef`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `SampleXRef` (
  `SampleId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `ProbeFreezeId` smallint(5) unsigned NOT NULL DEFAULT 0,
  PRIMARY KEY (`ProbeFreezeId`,`SampleId`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `SnpAll`
--

DROP TABLE IF EXISTS `SnpAll`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `SnpAll` (
  `Id` int(20) unsigned NOT NULL AUTO_INCREMENT,
  `SpeciesId` smallint(5) unsigned DEFAULT 1,
  `SnpName` char(30) DEFAULT NULL,
  `Rs` char(30) DEFAULT NULL,
  `Chromosome` char(2) DEFAULT NULL,
  `Position` double DEFAULT NULL,
  `Position_2016` double DEFAULT NULL,
  `Alleles` char(5) DEFAULT NULL,
  `Source` char(35) DEFAULT NULL,
  `ConservationScore` double DEFAULT NULL,
  `3Prime_UTR` text DEFAULT NULL,
  `5Prime_UTR` text DEFAULT NULL,
  `Upstream` text DEFAULT NULL,
  `Downstream` text DEFAULT NULL,
  `Intron` char(1) DEFAULT NULL,
  `Non_Splice_Site` text DEFAULT NULL,
  `Splice_Site` text DEFAULT NULL,
  `Intergenic` char(1) DEFAULT NULL,
  `Exon` char(1) DEFAULT NULL,
  `Non_Synonymous_Coding` text DEFAULT NULL,
  `Synonymous_Coding` text DEFAULT NULL,
  `Start_Gained` text DEFAULT NULL,
  `Start_Lost` text DEFAULT NULL,
  `Stop_Gained` text DEFAULT NULL,
  `Stop_Lost` text DEFAULT NULL,
  `Unknown_Effect_In_Exon` text DEFAULT NULL,
  `Domain` varchar(50) DEFAULT NULL,
  `Gene` varchar(30) DEFAULT NULL,
  `Transcript` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`Id`),
  FOREIGN KEY (SpeciesId) REFERENCES Species(SpeciesId),
  KEY `SnpName` (`SnpName`),
  KEY `Rs` (`Rs`),
  KEY `Position` (`Chromosome`,`Position`),
  KEY `Source` (`Source`)
) ENGINE=InnoDB AUTO_INCREMENT=84086331 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `SnpAllRat`
--

DROP TABLE IF EXISTS `SnpAllRat`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `SnpAllRat` (
  `Id` int(20) NOT NULL AUTO_INCREMENT,
  `SpeciesId` int(5) DEFAULT 2,
  `SnpName` char(30) DEFAULT NULL,
  `Chromosome` char(2) DEFAULT NULL,
  `Position` double DEFAULT NULL,
  `Alleles` char(5) DEFAULT NULL,
  `Source` char(35) DEFAULT NULL,
  `ConservationScore` double DEFAULT NULL,
  `Domain` varchar(50) DEFAULT NULL,
  `Gene` varchar(30) DEFAULT NULL,
  `Transcript` varchar(50) DEFAULT NULL,
  `Function` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`Id`),
  KEY `SnpName` (`SnpName`),
  KEY `Position` (`Chromosome`,`Position`),
  KEY `Source` (`Source`)
) ENGINE=MyISAM AUTO_INCREMENT=97663615 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `SnpAllele_to_be_deleted`
--

DROP TABLE IF EXISTS `SnpAllele_to_be_deleted`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `SnpAllele_to_be_deleted` (
  `Id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `Base` char(20) DEFAULT NULL,
  `Info` char(255) DEFAULT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=MyISAM AUTO_INCREMENT=11 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `SnpPattern`
--

DROP TABLE IF EXISTS `SnpPattern`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `SnpPattern` (
  `SnpId` int(10) unsigned NOT NULL DEFAULT 0,
  `129P2/OlaHsd` char(1) DEFAULT NULL,
  `129S1/SvImJ` char(1) DEFAULT NULL,
  `129S5/SvEvBrd` char(1) DEFAULT NULL,
  `AKR/J` char(1) DEFAULT NULL,
  `A/J` char(1) DEFAULT NULL,
  `BALB/cJ` char(1) DEFAULT NULL,
  `C3H/HeJ` char(1) DEFAULT NULL,
  `C57BL/6J` char(1) DEFAULT NULL,
  `CAST/EiJ` char(1) DEFAULT NULL,
  `CBA/J` char(1) DEFAULT NULL,
  `DBA/2J` char(1) DEFAULT NULL,
  `LP/J` char(1) DEFAULT NULL,
  `NOD/ShiLtJ` char(1) DEFAULT NULL,
  `NZO/HlLtJ` char(1) DEFAULT NULL,
  `PWK/PhJ` char(1) DEFAULT NULL,
  `SPRET/EiJ` char(1) DEFAULT NULL,
  `WSB/EiJ` char(1) DEFAULT NULL,
  `PWD/PhJ` char(1) DEFAULT NULL,
  `SJL/J` char(1) DEFAULT NULL,
  `NZL/LtJ` char(1) DEFAULT NULL,
  `CZECHII/EiJ` char(1) DEFAULT NULL,
  `CALB/RkJ` char(1) DEFAULT NULL,
  `ST/bJ` char(1) DEFAULT NULL,
  `ISS/IbgTejJ` char(1) DEFAULT NULL,
  `C57L/J` char(1) DEFAULT NULL,
  `Qsi5` char(1) DEFAULT NULL,
  `B6A6_Esline_Regeneron` char(1) DEFAULT NULL,
  `129T2/SvEmsJ` char(1) DEFAULT NULL,
  `BALB/cByJ` char(1) DEFAULT NULL,
  `NZB/BlNJ` char(1) DEFAULT NULL,
  `P/J` char(1) DEFAULT NULL,
  `I/LnJ` char(1) DEFAULT NULL,
  `PERC/EiJ` char(1) DEFAULT NULL,
  `TALLYHO/JngJ` char(1) DEFAULT NULL,
  `CE/J` char(1) DEFAULT NULL,
  `MRL/MpJ` char(1) DEFAULT NULL,
  `PERA/EiJ` char(1) DEFAULT NULL,
  `IS/CamRkJ` char(1) DEFAULT NULL,
  `ZALENDE/EiJ` char(1) DEFAULT NULL,
  `Fline` char(1) DEFAULT NULL,
  `BTBRT<+>tf/J` char(1) DEFAULT NULL,
  `O20` char(1) DEFAULT NULL,
  `C58/J` char(1) DEFAULT NULL,
  `BPH/2J` char(1) DEFAULT NULL,
  `DDK/Pas` char(1) DEFAULT NULL,
  `C57BL/6NHsd` char(1) DEFAULT NULL,
  `C57BL/6NTac` char(1) DEFAULT NULL,
  `129S4/SvJae` char(1) DEFAULT NULL,
  `BPL/1J` char(1) DEFAULT NULL,
  `BPN/3J` char(1) DEFAULT NULL,
  `PL/J` char(1) DEFAULT NULL,
  `DBA/1J` char(1) DEFAULT NULL,
  `MSM/Ms` char(1) DEFAULT NULL,
  `MA/MyJ` char(1) DEFAULT NULL,
  `NZW/LacJ` char(1) DEFAULT NULL,
  `C57BL/10J` char(1) DEFAULT NULL,
  `C57BL/6ByJ` char(1) DEFAULT NULL,
  `RF/J` char(1) DEFAULT NULL,
  `C57BR/cdJ` char(1) DEFAULT NULL,
  `129S6/SvEv` char(1) DEFAULT NULL,
  `MAI/Pas` char(1) DEFAULT NULL,
  `RIIIS/J` char(1) DEFAULT NULL,
  `C57BL/6NNIH` char(1) DEFAULT NULL,
  `FVB/NJ` char(1) DEFAULT NULL,
  `SEG/Pas` char(1) DEFAULT NULL,
  `MOLF/EiJ` char(1) DEFAULT NULL,
  `C3HeB/FeJ` char(1) DEFAULT NULL,
  `Lline` char(1) DEFAULT NULL,
  `SKIVE/EiJ` char(1) DEFAULT NULL,
  `C57BL/6NCrl` char(1) DEFAULT NULL,
  `KK/HlJ` char(1) DEFAULT NULL,
  `LG/J` char(1) DEFAULT NULL,
  `C57BLKS/J` char(1) DEFAULT NULL,
  `SM/J` char(1) DEFAULT NULL,
  `NOR/LtJ` char(1) DEFAULT NULL,
  `ILS/IbgTejJ` char(1) DEFAULT NULL,
  `C57BL/6JOlaHsd` char(1) DEFAULT NULL,
  `SWR/J` char(1) DEFAULT NULL,
  `C57BL/6JBomTac` char(1) DEFAULT NULL,
  `SOD1/EiJ` char(1) DEFAULT NULL,
  `NON/LtJ` char(1) DEFAULT NULL,
  `JF1/Ms` char(1) DEFAULT NULL,
  `129X1/SvJ` char(1) DEFAULT NULL,
  `C2T1_Esline_Nagy` char(1) DEFAULT NULL,
  `C57BL/6NJ` char(1) DEFAULT NULL,
  `LEWES/EiJ` char(1) DEFAULT NULL,
  `RBA/DnJ` char(1) DEFAULT NULL,
  `DDY/JclSidSeyFrkJ` char(1) DEFAULT NULL,
  `SEA/GnJ` char(1) DEFAULT NULL,
  `C57BL/6JCrl` char(1) DEFAULT NULL,
  `EL/SuzSeyFrkJ` char(1) DEFAULT NULL,
  `HTG/GoSfSnJ` char(1) DEFAULT NULL,
  `129S2/SvHsd` char(1) DEFAULT NULL,
  `MOLG/DnJ` char(1) DEFAULT NULL,
  `BUB/BnJ` char(1) DEFAULT NULL,
  PRIMARY KEY (`SnpId`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `SnpSource`
--

DROP TABLE IF EXISTS `SnpSource`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `SnpSource` (
  `Id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `Name` char(35) DEFAULT NULL,
  `DateCreated` date DEFAULT NULL,
  `DateAdded` date DEFAULT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=MyISAM AUTO_INCREMENT=29 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Species`
--

DROP TABLE IF EXISTS `Species`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Species` (
  `Id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `SpeciesId` int(5) DEFAULT NULL,
  `SpeciesName` varchar(50) DEFAULT NULL,
  `Name` char(30) NOT NULL DEFAULT '',
  `MenuName` char(50) DEFAULT NULL,
  `FullName` char(100) NOT NULL DEFAULT '',
  `TaxonomyId` int(11) DEFAULT NULL,
  `OrderId` smallint(6) DEFAULT NULL,
  PRIMARY KEY (`Id`),
  KEY `Name` (`Name`)
) ENGINE=MyISAM AUTO_INCREMENT=11 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Strain`
--

DROP TABLE IF EXISTS `Strain`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Strain` (
  `Id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `Name` varchar(100) DEFAULT NULL,
  `Name2` varchar(100) DEFAULT NULL,
  `SpeciesId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `Symbol` char(5) DEFAULT NULL,
  `Alias` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`Id`),
  UNIQUE KEY `Name` (`Name`,`SpeciesId`),
  FOREIGN KEY (SpeciesId) REFERENCES Species(SpeciesId),
  KEY `Symbol` (`Symbol`)
) ENGINE=MyISAM AUTO_INCREMENT=63438 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `StrainXRef`
--

DROP TABLE IF EXISTS `StrainXRef`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `StrainXRef` (
  `InbredSetId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `StrainId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `OrderId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `Used_for_mapping` char(1) DEFAULT 'N',
  `PedigreeStatus` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`InbredSetId`,`StrainId`),
  UNIQUE KEY `Orders` (`InbredSetId`,`OrderId`),
  FOREIGN KEY (InbredSetId) REFERENCES InbredSet(InbredSetId),
  FOREIGN KEY (StrainId) REFERENCES Strain(Id)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `TableComments`
--

DROP TABLE IF EXISTS `TableComments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `TableComments` (
  `TableName` varchar(100) NOT NULL DEFAULT '',
  `Comment` text DEFAULT NULL,
  PRIMARY KEY (`TableName`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `TableFieldAnnotation`
--

DROP TABLE IF EXISTS `TableFieldAnnotation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `TableFieldAnnotation` (
  `TableField` varchar(100) NOT NULL DEFAULT '',
  `Foreign_Key` varchar(100) DEFAULT NULL,
  `Annotation` text DEFAULT NULL,
  PRIMARY KEY (`TableField`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Temp`
--

DROP TABLE IF EXISTS `Temp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Temp` (
  `Id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `dbdisplayname` varchar(255) DEFAULT NULL,
  `Name` varchar(30) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `createtime` datetime NOT NULL DEFAULT '2004-01-01 12:00:00',
  `DataId` int(11) NOT NULL DEFAULT 0,
  `InbredSetId` smallint(5) unsigned NOT NULL DEFAULT 1,
  `IP` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`Id`),
  UNIQUE KEY `Name` (`Name`),
  FOREIGN KEY (InbredSetId) REFERENCES InbredSet(InbredSetId)
) ENGINE=MyISAM AUTO_INCREMENT=98608 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `TempData`
--

DROP TABLE IF EXISTS `TempData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `TempData` (
  `Id` int(10) unsigned NOT NULL DEFAULT 0,
  `StrainId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `value` double NOT NULL DEFAULT 0,
  `SE` double DEFAULT NULL,
  `NStrain` smallint(6) DEFAULT NULL,
  UNIQUE KEY `DataId` (`Id`,`StrainId`),
  FOREIGN KEY (StrainId) REFERENCES Strain(Id)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Tissue`
--

DROP TABLE IF EXISTS `Tissue`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Tissue` (
  `Id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `TissueId` int(5) DEFAULT NULL,
  `TissueName` varchar(50) DEFAULT NULL,
  `Name` char(50) DEFAULT NULL,
  `Short_Name` char(30) NOT NULL DEFAULT '',
  `BIRN_lex_ID` char(30) DEFAULT NULL,
  `BIRN_lex_Name` char(30) DEFAULT NULL,
  PRIMARY KEY (`Id`),
  UNIQUE KEY `Short_Name` (`Short_Name`),
  UNIQUE KEY `Name` (`Name`)
) ENGINE=MyISAM AUTO_INCREMENT=180 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `TissueProbeFreeze`
--

DROP TABLE IF EXISTS `TissueProbeFreeze`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `TissueProbeFreeze` (
  `Id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `ChipId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `StrainId` varchar(100) NOT NULL DEFAULT '0',
  `Name` varchar(100) NOT NULL DEFAULT '',
  `FullName` varchar(100) NOT NULL DEFAULT '',
  `ShortName` varchar(100) NOT NULL DEFAULT '',
  `CreateTime` date NOT NULL DEFAULT '0000-00-00',
  `InbredSetId` smallint(5) unsigned DEFAULT 1,
  PRIMARY KEY (`Id`),
  UNIQUE KEY `Name` (`Name`),
  UNIQUE KEY `FullName` (`FullName`),
  FOREIGN KEY (StrainId) REFERENCES Strain(Id)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `TissueProbeSetData`
--

DROP TABLE IF EXISTS `TissueProbeSetData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `TissueProbeSetData` (
  `Id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `TissueID` int(10) unsigned NOT NULL DEFAULT 0,
  `value` float NOT NULL DEFAULT 0,
  PRIMARY KEY (`Id`,`TissueID`),
  FOREIGN KEY (TissueID) REFERENCES Tissue(TissueId)
) ENGINE=MyISAM AUTO_INCREMENT=90563 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `TissueProbeSetFreeze`
--

DROP TABLE IF EXISTS `TissueProbeSetFreeze`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `TissueProbeSetFreeze` (
  `Id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `TissueProbeFreezeId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `AvgID` smallint(5) unsigned NOT NULL DEFAULT 0,
  `Name` varchar(40) DEFAULT NULL,
  `Name2` varchar(100) NOT NULL DEFAULT '',
  `FullName` varchar(100) NOT NULL DEFAULT '',
  `ShortName` varchar(100) NOT NULL DEFAULT '',
  `CreateTime` date NOT NULL DEFAULT '0000-00-00',
  `public` tinyint(4) NOT NULL DEFAULT 0,
  `confidentiality` tinyint(4) NOT NULL DEFAULT 0,
  `AuthorisedUsers` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`Id`),
  UNIQUE KEY `FullName` (`FullName`),
  UNIQUE KEY `Name` (`Name`),
  FOREIGN KEY (TissueProbeFreezeId) REFERENCES TissueProbeFreeze(Id),
  KEY `NameIndex` (`Name2`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `TissueProbeSetXRef`
--

DROP TABLE IF EXISTS `TissueProbeSetXRef`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `TissueProbeSetXRef` (
  `TissueProbeSetFreezeId` smallint(5) unsigned NOT NULL DEFAULT 0,
  `ProbesetId` int(10) unsigned NOT NULL DEFAULT 0,
  `DataId` int(10) unsigned NOT NULL DEFAULT 0,
  `Mean` float DEFAULT 0,
  `useStatus` char(1) DEFAULT NULL,
  `Symbol` varchar(100) DEFAULT NULL,
  `GeneId` varchar(20) DEFAULT NULL,
  `Chr` char(3) DEFAULT NULL,
  `Mb` double DEFAULT NULL,
  `Mb_2016` double DEFAULT NULL,
  `description` varchar(255) DEFAULT NULL,
  `Probe_Target_Description` varchar(225) DEFAULT NULL,
  PRIMARY KEY (`TissueProbeSetFreezeId`,`ProbesetId`),
  UNIQUE KEY `DataId_IDX` (`DataId`),
  FOREIGN KEY (TissueProbeSetFreezeId) REFERENCES TissueProbeSetFreeze(Id),
  FOREIGN KEY (ProbesetId) REFERENCES ProbeSet(Id),
  KEY `symbol_IDX` (`Symbol`),
  KEY `GeneId_IDX` (`GeneId`),
  KEY `Position` (`Chr`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `TraitMetadata`
--

DROP TABLE IF EXISTS `TraitMetadata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `TraitMetadata` (
  `type` varchar(255) DEFAULT NULL,
  `value` longtext DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `User`
--

DROP TABLE IF EXISTS `User`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `User` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL DEFAULT '',
  `password` varchar(100) NOT NULL DEFAULT '',
  `email` varchar(100) DEFAULT NULL,
  `createtime` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `user_ip` varchar(20) DEFAULT NULL,
  `lastlogin` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `disable` enum('Y','N') DEFAULT 'N',
  `privilege` enum('guest','user','admin','root') DEFAULT NULL,
  `grpName` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_index` (`name`)
) ENGINE=MyISAM AUTO_INCREMENT=353 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `UserPrivilege`
--

DROP TABLE IF EXISTS `UserPrivilege`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `UserPrivilege` (
  `UserId` int(10) unsigned NOT NULL,
  `ProbeSetFreezeId` smallint(5) unsigned NOT NULL,
  `download_result_priv` enum('N','Y') NOT NULL DEFAULT 'N',
  KEY `userId` (`UserId`,`ProbeSetFreezeId`),
  FOREIGN KEY (UserId) REFERENCES User(id),
  FOREIGN KEY (ProbeSetFreezeId) REFERENCES ProbeSetFreeze(Id)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Vlookup`
--

DROP TABLE IF EXISTS `Vlookup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Vlookup` (
  `Id` int(11) NOT NULL AUTO_INCREMENT,
  `VLProbeSetId` text DEFAULT NULL,
  `VLBlatSeq` longtext DEFAULT NULL,
  `InfoFileId` int(5) DEFAULT NULL,
  `DatasetId` int(5) DEFAULT NULL,
  `SpeciesId` int(5) DEFAULT NULL,
  `TissueId` int(5) DEFAULT NULL,
  `InbredSetId` int(5) DEFAULT NULL,
  `GeneChipId` int(5) DEFAULT NULL,
  `AvgMethodId` int(5) DEFAULT NULL,
  `InfoPageName` varchar(255) DEFAULT NULL,
  `GN_AccesionId` int(5) DEFAULT NULL,
  `Name` varchar(100) DEFAULT NULL,
  `GeneId` varchar(10) DEFAULT NULL,
  `Mb` double DEFAULT NULL,
  `Chr` varchar(10) DEFAULT NULL,
  `Probe_set_Blat_Mb_start` double DEFAULT NULL,
  `Probe_set_Blat_Mb_end` double DEFAULT NULL,
  `Strand` char(1) DEFAULT NULL,
  `TxStart` double DEFAULT NULL,
  `TxEnd` double DEFAULT NULL,
  `cdsStart` double DEFAULT NULL,
  `cdsEnd` double DEFAULT NULL,
  `exonCount` int(7) DEFAULT NULL,
  `exonStarts` text DEFAULT NULL,
  `exonEnds` text DEFAULT NULL,
  `ProteinID` varchar(15) DEFAULT NULL,
  `AlignID` varchar(10) DEFAULT NULL,
  `kgID` varchar(10) DEFAULT NULL,
  `NM_ID` varchar(15) DEFAULT NULL,
  `SnpName` char(30) DEFAULT NULL,
  `Position` double DEFAULT NULL,
  `HMDB_ID` varchar(255) DEFAULT NULL,
  `Symbol` varchar(100) DEFAULT NULL,
  `description` longtext DEFAULT NULL,
  `alias` longtext DEFAULT NULL,
  `Full_Description` longtext DEFAULT NULL,
  `BlatSeq` text DEFAULT NULL,
  `ChEBI_ID` int(10) DEFAULT NULL,
  `ChEMBL_ID` varchar(100) DEFAULT NULL,
  `CAS_number` varchar(100) DEFAULT NULL,
  `PubChem_ID` int(10) DEFAULT NULL,
  `ChemSpider_ID` varchar(10) DEFAULT NULL,
  `UNII_ID` varchar(100) DEFAULT NULL,
  `EC_number` varchar(100) DEFAULT NULL,
  `KEGG_ID` varchar(100) DEFAULT NULL,
  `Molecular_Weight` varchar(100) DEFAULT NULL,
  `Nugowiki_ID` varchar(100) DEFAULT NULL,
  `assembly` varchar(10) DEFAULT NULL,
  KEY `Id` (`Id`)
) ENGINE=MyISAM AUTO_INCREMENT=753474564 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `login`
--

DROP TABLE IF EXISTS `login`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `login` (
  `id` varchar(36) NOT NULL,
  `user` varchar(36) DEFAULT NULL,
  `timestamp` datetime DEFAULT NULL,
  `ip_address` varchar(39) DEFAULT NULL,
  `successful` tinyint(1) NOT NULL,
  `session_id` text DEFAULT NULL,
  `assumed_by` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY (user) REFERENCES user(id),
  KEY `user` (`user`),
  KEY `assumed_by` (`assumed_by`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `metadata_audit`
--

DROP TABLE IF EXISTS `metadata_audit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `metadata_audit` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dataset_id` int(11) NOT NULL,
  `editor` varchar(255) NOT NULL,
  `json_diff_data` varchar(2048) NOT NULL,
  `time_stamp` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  CONSTRAINT `CONSTRAINT_1` CHECK (json_valid(`json_diff_data`))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `pubmedsearch`
--

DROP TABLE IF EXISTS `pubmedsearch`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `pubmedsearch` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `pubmedid` bigint(20) DEFAULT NULL,
  `title` text DEFAULT NULL,
  `authorfullname` text DEFAULT NULL,
  `authorshortname` text DEFAULT NULL,
  `institute` text DEFAULT NULL,
  `geneid` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `NewIndex4` (`geneid`),
  FULLTEXT KEY `NewIndex1` (`institute`),
  FULLTEXT KEY `NewIndex3` (`authorfullname`,`authorshortname`)
) ENGINE=MyISAM AUTO_INCREMENT=1401371 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `role`
--

DROP TABLE IF EXISTS `role`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `role` (
  `the_id` varchar(36) NOT NULL,
  `name` varchar(80) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`the_id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `roles_users`
--

DROP TABLE IF EXISTS `roles_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `roles_users` (
  `user_id` int(11) DEFAULT NULL,
  `role_id` int(11) DEFAULT NULL,
  KEY `user_id` (`user_id`),
  KEY `role_id` (`role_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `temporary`
--

DROP TABLE IF EXISTS `temporary`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `temporary` (
  `tax_id` varchar(20) DEFAULT NULL,
  `GeneID` varchar(20) DEFAULT NULL,
  `Symbol` varchar(100) DEFAULT NULL,
  `OMIM` varchar(100) DEFAULT NULL,
  `HomoloGene` varchar(100) DEFAULT NULL,
  `Other_GeneID` varchar(20) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user` (
  `id` varchar(36) NOT NULL,
  `email_address` varchar(50) NOT NULL,
  `password` text NOT NULL,
  `full_name` varchar(50) DEFAULT NULL,
  `organization` varchar(50) DEFAULT NULL,
  `active` tinyint(1) NOT NULL,
  `registration_info` text DEFAULT NULL,
  `confirmed` text DEFAULT NULL,
  `superuser` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email_address` (`email_address`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_collection`
--

DROP TABLE IF EXISTS `user_collection`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_collection` (
  `id` varchar(36) NOT NULL,
  `user` varchar(36) DEFAULT NULL,
  `name` text DEFAULT NULL,
  `created_timestamp` datetime DEFAULT NULL,
  `changed_timestamp` datetime DEFAULT NULL,
  `members` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY (user) REFERENCES user(id),
  KEY `user` (`user`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_openids`
--

DROP TABLE IF EXISTS `user_openids`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_openids` (
  `openid_url` varchar(255) NOT NULL,
  `user_id` varchar(36) NOT NULL,
  PRIMARY KEY (`openid_url`),
  FOREIGN KEY (user_id) REFERENCES user(id),
  KEY `user_id` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2021-07-14  5:26:53
