-- Forest Fire database backup
-- Created at: 2026-03-09 21:49:38
-- Dialect: mysql

-- Table: alert
DROP TABLE IF EXISTS `alert`;
CREATE TABLE `alert` (
  `id` int NOT NULL AUTO_INCREMENT,
  `timestamp` datetime NOT NULL,
  `image_path` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `yolo_confidence` float NOT NULL,
  `camera_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `llm_result` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `remark` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=433 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (327, '2026-03-08 22:41:58', '/static/fire_1_20260308_224158.jpg', 0.820752, '东区瞭望塔', '【AI高危建议】YOLO 置信度 82.1% ≥ 80%，建议优先现场核实。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (328, '2026-03-08 22:42:12', '/static/fire_1_20260308_224211.jpg', 0.677019, '东区瞭望塔', '【AI建议】疑似真实火灾，需现场核实。
判定结果：真实火灾
分析说明：明火、浓烟及参与灭火人员表明燃火。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (329, '2026-03-08 22:42:22', '/static/fire_1_20260308_224221.jpg', 0.622206, '东区瞭望塔', '大模型调用内部错误: ', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (330, '2026-03-08 22:42:35', '/static/fire_1_20260308_224234.jpg', 0.646107, '东区瞭望塔', '【AI建议】疑似误报，仍需人工复核。
误报', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (331, '2026-03-08 22:42:45', '/static/fire_1_20260308_224244.jpg', 0.555963, '东区瞭望塔', '大模型调用内部错误: ', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (332, '2026-03-08 22:42:55', '/static/fire_1_20260308_224254.jpg', 0.872722, '东区瞭望塔', '【AI高危建议】YOLO 置信度 87.3% ≥ 80%，建议优先现场核实。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (333, '2026-03-08 22:43:05', '/static/fire_1_20260308_224304.jpg', 0.885914, '东区瞭望塔', '【AI高危建议】YOLO 置信度 88.6% ≥ 80%，建议优先现场核实。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (334, '2026-03-08 22:43:15', '/static/fire_1_20260308_224314.jpg', 0.664502, '东区瞭望塔', '【AI建议】疑似真实火灾，需现场核实。
判定结果：真实火灾
分析说明：火光透过浓烟显现。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (335, '2026-03-08 22:43:28', '/static/fire_1_20260308_224327.jpg', 0.550945, '东区瞭望塔', '【AI建议】疑似真实火灾，需现场核实。
判定结果：真实火灾
分析说明：有明火和浓烟，周围植被干燥易燃。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (336, '2026-03-08 22:43:56', '/static/fire_1_20260308_224355.jpg', 0.820752, '东区瞭望塔', '【AI高危建议】YOLO 置信度 82.1% ≥ 80%，建议优先现场核实。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (337, '2026-03-08 22:44:09', '/static/fire_1_20260308_224409.jpg', 0.757751, '东区瞭望塔', '【AI建议】疑似真实火灾，需现场核实。
判定结果：真实火灾
分析说明：明火、浓烟，人员在灭火。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (338, '2026-03-08 22:44:19', '/static/fire_1_20260308_224419.jpg', 0.539445, '东区瞭望塔', '【AI建议】疑似真实火灾，需现场核实。
判定结果：真实火灾

分析说明：浓烟和日出时分明显的红光提示非自然灾害。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (339, '2026-03-08 22:44:32', '/static/fire_1_20260308_224432.jpg', 0.624347, '东区瞭望塔', '【AI建议】疑似误报，仍需人工复核。
判定结果：误报
分析说明：这是支持白盔队的图标，并非森林火灾图片。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (340, '2026-03-08 22:44:42', '/static/fire_1_20260308_224442.jpg', 0.43045, '东区瞭望塔', '【AI建议】疑似真实火灾，需现场核实。
判定结果：真实火灾

分析说明：火焰明顶部、浓烟滚滚。', 'verified_true', '【现场核实】真实火灾（2026-03-08 23:20:44）
真实火灾');
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (341, '2026-03-08 22:44:52', '/static/fire_1_20260308_224452.jpg', 0.874064, '东区瞭望塔', '【AI高危建议】YOLO 置信度 87.4% ≥ 80%，建议优先现场核实。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (342, '2026-03-08 22:45:02', '/static/fire_1_20260308_224502.jpg', 0.833155, '东区瞭望塔', '【AI高危建议】YOLO 置信度 83.3% ≥ 80%，建议优先现场核实。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (343, '2026-03-08 22:45:15', '/static/fire_1_20260308_224515.jpg', 0.425841, '东区瞭望塔', '【AI建议】疑似真实火灾，需现场核实。
判定结果：真实火灾
分析说明：灰霾，片面遮挡，无法排除火灾发生可能性。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (344, '2026-03-08 22:45:28', '/static/fire_1_20260308_224528.jpg', 0.876287, '东区瞭望塔', '【AI高危建议】YOLO 置信度 87.6% ≥ 80%，建议优先现场核实。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (345, '2026-03-08 22:45:38', '/static/fire_1_20260308_224538.jpg', 0.731728, '东区瞭望塔', '【AI建议】疑似真实火灾，需现场核实。
判定结果：真实火灾
分析说明：有浓烟、明火和灭火直升机。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (346, '2026-03-08 22:45:54', '/static/fire_1_20260308_224554.jpg', 0.862773, '东区瞭望塔', '【AI高危建议】YOLO 置信度 86.3% ≥ 80%，建议优先现场核实。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (347, '2026-03-08 22:46:04', '/static/fire_1_20260308_224604.jpg', 0.821897, '东区瞭望塔', '【AI高危建议】YOLO 置信度 82.2% ≥ 80%，建议优先现场核实。', 'dispatched', '【高风险直联】YOLO置信度 82.2% >= 80%，允许直接联动。
【联动消防】已通知林区消防队（2026-03-08 22:54:42）；联系人：5556666');
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (348, '2026-03-09 21:03:11', '/static/fire_1_20260309_210310.jpg', 0.58436, '东区瞭望塔', '[风险级别:中风险] 风险级别: 中风险
处置建议: 以人为本，优先疏散灾民，提供紧急救援。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (349, '2026-03-09 21:03:24', '/static/fire_1_20260309_210323.jpg', 0.717559, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险
处置建议: 优先疏散居民，尽快增派消防人员，安排空中洒水灭火。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (350, '2026-03-09 21:03:34', '/static/fire_1_20260309_210333.jpg', 0.90899, '东区瞭望塔', '[风险级别:高风险] YOLO置信度 90.9% > 80%，直接判定高风险并进入人工处置。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (351, '2026-03-09 21:03:44', '/static/fire_1_20260309_210344.jpg', 0.705617, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险

处置建议: 立即组织消防力量，加强现场监控。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (352, '2026-03-09 21:03:57', '/static/fire_1_20260309_210357.jpg', 0.843037, '东区瞭望塔', '[风险级别:高风险] YOLO置信度 84.3% > 80%，直接判定高风险并进入人工处置。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (353, '2026-03-09 21:04:07', '/static/fire_1_20260309_210407.jpg', 0.821186, '东区瞭望塔', '[风险级别:高风险] YOLO置信度 82.1% > 80%，直接判定高风险并进入人工处置。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (354, '2026-03-09 21:04:26', '/static/fire_1_20260309_210426.jpg', 0.34188, '东区瞭望塔', '[风险级别:低风险] YOLO置信度 34.2% < 40%，自动静默归档。', 'archived_low', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (355, '2026-03-09 21:04:36', '/static/fire_1_20260309_210436.jpg', 0.8437, '东区瞭望塔', '[风险级别:高风险] YOLO置信度 84.4% > 80%，直接判定高风险并进入人工处置。', 'resolved', '【SOP1 已执行】2026-03-09 21:06:12 完成人工视检，已联动消防（电话:119），并完成内部调度。状态变更为已处理。
接警人:Lee；调度对象:当日护林员；处理完成');
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (356, '2026-03-09 21:04:46', '/static/fire_1_20260309_210446.jpg', 0.723929, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险
处置建议: 增派人力，加大灭火资源，加强监测，防止蔓延', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (357, '2026-03-09 21:04:56', '/static/fire_1_20260309_210456.jpg', 0.60596, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险
处置建议: 增加监控，彻查火源；加强消防力量。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (358, '2026-03-09 21:05:06', '/static/fire_1_20260309_210506.jpg', 0.521826, '东区瞭望塔', '[风险级别:中风险] 风险级别: 中风险
处置建议: 加强防火措施，定期检查设备，合理配置人员。', 'verified_false', '【SOP2 已执行-确认为误报】2026-03-09 21:06:46 完成现场复核，确认误报并归档处理。
复核人:Operator2；误报原因:反光；已处理');
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (359, '2026-03-09 21:05:16', '/static/fire_1_20260309_210516.jpg', 0.666021, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险
处置建议: 紧急疏散、防火隔离、水源保障。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (360, '2026-03-09 21:05:26', '/static/fire_1_20260309_210526.jpg', 0.855167, '东区瞭望塔', '[风险级别:高风险] YOLO置信度 85.5% > 80%，直接判定高风险并进入人工处置。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (361, '2026-03-09 21:05:36', '/static/fire_1_20260309_210536.jpg', 0.880604, '东区瞭望塔', '[风险级别:高风险] YOLO置信度 88.1% > 80%，直接判定高风险并进入人工处置。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (362, '2026-03-09 21:05:59', '/static/fire_1_20260309_210558.jpg', 0.780011, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险
处置建议: 扩大隔离带，增派消防队伍，建立疏散机制。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (363, '2026-03-09 21:06:15', '/static/fire_1_20260309_210614.jpg', 0.570882, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险
处置建议: 加强监测，疏散人群，准备消防物资。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (364, '2026-03-09 21:06:25', '/static/fire_1_20260309_210624.jpg', 0.299316, '东区瞭望塔', '[风险级别:低风险] YOLO置信度 29.9% < 40%，自动静默归档。', 'archived_low', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (365, '2026-03-09 21:06:41', '/static/fire_1_20260309_210640.jpg', 0.705063, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险  
处置建议: 调动更多资源，迅速采取行动灭火，保护居民和重要设施。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (366, '2026-03-09 21:06:51', '/static/fire_1_20260309_210650.jpg', 0.638172, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险
处置建议: 增加监控频次，准备应急预案。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (367, '2026-03-09 21:07:04', '/static/fire_1_20260309_210703.jpg', 0.601411, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险
处置建议: 加强监测，及时疏散群众，准备应急救援力量。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (368, '2026-03-09 21:07:14', '/static/fire_1_20260309_210713.jpg', 0.602943, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险  
处置建议: 调集力量，迅速灭火，防止扩散。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (369, '2026-03-09 21:07:24', '/static/fire_1_20260309_210723.jpg', 0.871303, '东区瞭望塔', '[风险级别:高风险] YOLO置信度 87.1% > 80%，直接判定高风险并进入人工处置。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (370, '2026-03-09 21:07:34', '/static/fire_1_20260309_210733.jpg', 0.822904, '东区瞭望塔', '[风险级别:高风险] YOLO置信度 82.3% > 80%，直接判定高风险并进入人工处置。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (371, '2026-03-09 21:07:50', '/static/fire_1_20260309_210749.jpg', 0.559558, '东区瞭望塔', '[风险级别:中风险] 风险级别: 中风险
处置建议: 加强监测预警，及时疏散人员，撤离车辆。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (372, '2026-03-09 21:08:00', '/static/fire_1_20260309_210759.jpg', 0.883744, '东区瞭望塔', '[风险级别:高风险] YOLO置信度 88.4% > 80%，直接判定高风险并进入人工处置。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (373, '2026-03-09 21:08:10', '/static/fire_1_20260309_210810.jpg', 0.3203, '东区瞭望塔', '[风险级别:低风险] YOLO置信度 32.0% < 40%，自动静默归档。', 'archived_low', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (374, '2026-03-09 21:08:20', '/static/fire_1_20260309_210820.jpg', 0.319019, '东区瞭望塔', '[风险级别:低风险] YOLO置信度 31.9% < 40%，自动静默归档。', 'archived_low', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (375, '2026-03-09 21:08:36', '/static/fire_1_20260309_210836.jpg', 0.792984, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险
处置建议: 及时疏散居民，加强消防设备使用，加强监控。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (376, '2026-03-09 21:08:46', '/static/fire_1_20260309_210846.jpg', 0.590569, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险
处置建议: 强化监测，制定应急预案，组织消防准备。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (377, '2026-03-09 21:08:59', '/static/fire_1_20260309_210859.jpg', 0.462656, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险
处置建议: 加强监控，准备消防设备，组织紧急疏散。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (378, '2026-03-09 21:09:09', '/static/fire_1_20260309_210909.jpg', 0.73916, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险
处置建议: 增加消防力量，立即进行扑救。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (379, '2026-03-09 21:09:19', '/static/fire_1_20260309_210919.jpg', 0.876482, '东区瞭望塔', '[风险级别:高风险] YOLO置信度 87.6% > 80%，直接判定高风险并进入人工处置。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (380, '2026-03-09 21:09:29', '/static/fire_1_20260309_210929.jpg', 0.785003, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险
处置建议: 加强监控，迅速扑灭大火。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (381, '2026-03-09 21:09:45', '/static/fire_1_20260309_210945.jpg', 0.447262, '东区瞭望塔', '[风险级别:中风险] 风险级别: 中风险
处置建议: 增加森林防火设施，提高灭火效率。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (382, '2026-03-09 21:09:55', '/static/fire_1_20260309_210955.jpg', 0.878223, '东区瞭望塔', '[风险级别:高风险] YOLO置信度 87.8% > 80%，直接判定高风险并进入人工处置。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (383, '2026-03-09 21:10:08', '/static/fire_1_20260309_211008.jpg', 0.265736, '东区瞭望塔', '[风险级别:低风险] YOLO置信度 26.6% < 40%，自动静默归档。', 'archived_low', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (384, '2026-03-09 21:10:18', '/static/fire_1_20260309_211018.jpg', 0.295932, '东区瞭望塔', '[风险级别:低风险] YOLO置信度 29.6% < 40%，自动静默归档。', 'archived_low', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (385, '2026-03-09 21:10:34', '/static/fire_1_20260309_211034.jpg', 0.668135, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险
处置建议: 加强监测，迅速增援，防止火势扩大。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (386, '2026-03-09 21:10:45', '/static/fire_1_20260309_211044.jpg', 0.568302, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险  
处置建议: 增加专职消防救援力量，紧急疏散居民，及时扑灭火源。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (387, '2026-03-09 21:10:58', '/static/fire_1_20260309_211057.jpg', 0.601085, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险
处置建议: 增加监控频率，提前部署灭火设施。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (388, '2026-03-09 21:11:08', '/static/fire_1_20260309_211107.jpg', 0.451006, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险
处置建议: 提高巡护频率，加强消防设施准备。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (389, '2026-03-09 21:11:18', '/static/fire_1_20260309_211117.jpg', 0.880223, '东区瞭望塔', '[风险级别:高风险] YOLO置信度 88.0% > 80%，直接判定高风险并进入人工处置。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (390, '2026-03-09 21:11:28', '/static/fire_1_20260309_211127.jpg', 0.765841, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险

处置建议: 增加消防人员，调度飞机灭火。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (391, '2026-03-09 21:11:38', '/static/fire_1_20260309_211137.jpg', 0.459911, '东区瞭望塔', '[风险级别:中风险] 风险级别: 中风险
处置建议: 加强监控，准备消防器材，及时扑救。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (392, '2026-03-09 21:11:54', '/static/fire_1_20260309_211153.jpg', 0.861824, '东区瞭望塔', '[风险级别:高风险] YOLO置信度 86.2% > 80%，直接判定高风险并进入人工处置。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (393, '2026-03-09 21:12:04', '/static/fire_1_20260309_211203.jpg', 0.329749, '东区瞭望塔', '[风险级别:低风险] YOLO置信度 33.0% < 40%，自动静默归档。', 'archived_low', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (394, '2026-03-09 21:12:14', '/static/fire_1_20260309_211213.jpg', 0.435721, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险
处置建议: 加大消防力量，确保随时能够扑灭火灾。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (395, '2026-03-09 21:12:30', '/static/fire_1_20260309_211229.jpg', 0.776717, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险
处置建议: 加强野外火源管理和巡查，及时扑救森林火灾。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (396, '2026-03-09 21:12:40', '/static/fire_1_20260309_211239.jpg', 0.532831, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险
处置建议: 增强森林火灾预警系统，强化防火意识与物资准备。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (397, '2026-03-09 21:12:53', '/static/fire_1_20260309_211252.jpg', 0.735532, '东区瞭望塔', '[风险级别:中风险] 风险级别: 中风险
处置建议: 及时疏散，加强监测。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (398, '2026-03-09 21:13:03', '/static/fire_1_20260309_211302.jpg', 0.377505, '东区瞭望塔', '[风险级别:低风险] YOLO置信度 37.8% < 40%，自动静默归档。', 'archived_low', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (399, '2026-03-09 21:13:13', '/static/fire_1_20260309_211312.jpg', 0.678801, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险  
处置建议: 立即增援、加强监测、组织人员撤离。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (400, '2026-03-09 21:13:23', '/static/fire_1_20260309_211323.jpg', 0.822079, '东区瞭望塔', '[风险级别:高风险] YOLO置信度 82.2% > 80%，直接判定高风险并进入人工处置。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (401, '2026-03-09 21:13:33', '/static/fire_1_20260309_211333.jpg', 0.378683, '东区瞭望塔', '[风险级别:低风险] YOLO置信度 37.9% < 40%，自动静默归档。', 'archived_low', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (402, '2026-03-09 21:13:46', '/static/fire_1_20260309_211346.jpg', 0.764409, '东区瞭望塔', '[风险级别:中风险] 风险级别: 中风险
处置建议: 增加人手，加强监测，及时扑灭火源。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (403, '2026-03-09 21:13:56', '/static/fire_1_20260309_211356.jpg', 0.263243, '东区瞭望塔', '[风险级别:低风险] YOLO置信度 26.3% < 40%，自动静默归档。', 'archived_low', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (404, '2026-03-09 21:14:12', '/static/fire_1_20260309_211412.jpg', 0.34772, '东区瞭望塔', '[风险级别:低风险] YOLO置信度 34.8% < 40%，自动静默归档。', 'archived_low', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (405, '2026-03-09 21:14:28', '/static/fire_1_20260309_211428.jpg', 0.748845, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险
处置建议: 增加消防人员和物资，确保预警系统有效性。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (406, '2026-03-09 21:14:38', '/static/fire_1_20260309_211438.jpg', 0.590764, '东区瞭望塔', '[风险级别:中风险] 风险级别: 中风险
处置建议: 增强预警机制，加强森林护林员配备。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (407, '2026-03-09 21:14:48', '/static/fire_1_20260309_211448.jpg', 0.25257, '东区瞭望塔', '[风险级别:低风险] YOLO置信度 25.3% < 40%，自动静默归档。', 'archived_low', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (408, '2026-03-09 21:14:58', '/static/fire_1_20260309_211458.jpg', 0.669873, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险
处置建议: 立即疏散，组织消防力量，部署直升机灭火。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (409, '2026-03-09 21:15:11', '/static/fire_1_20260309_211511.jpg', 0.805877, '东区瞭望塔', '[风险级别:高风险] YOLO置信度 80.6% > 80%，直接判定高风险并进入人工处置。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (410, '2026-03-09 21:15:21', '/static/fire_1_20260309_211521.jpg', 0.725308, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险
处置建议: 紧急疏散、增加消防力量、水源准备、实时监测。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (411, '2026-03-09 21:15:31', '/static/fire_1_20260309_211531.jpg', 0.349052, '东区瞭望塔', '[风险级别:低风险] YOLO置信度 34.9% < 40%，自动静默归档。', 'archived_low', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (412, '2026-03-09 21:15:44', '/static/fire_1_20260309_211544.jpg', 0.453287, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险
处置建议: 迅速部署消防力量灭火，加强重点区域监控。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (413, '2026-03-09 21:16:10', '/static/fire_1_20260309_211609.jpg', 0.296796, '东区瞭望塔', '[风险级别:低风险] YOLO置信度 29.7% < 40%，自动静默归档。', 'archived_low', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (414, '2026-03-09 21:16:26', '/static/fire_1_20260309_211625.jpg', 0.673988, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险
处置建议: 增加更多消防员和装备，尽快控制火势。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (415, '2026-03-09 21:16:36', '/static/fire_1_20260309_211635.jpg', 0.629535, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险
处置建议: 增加防火设施，定期检查林区。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (416, '2026-03-09 21:16:46', '/static/fire_1_20260309_211645.jpg', 0.273298, '东区瞭望塔', '[风险级别:低风险] YOLO置信度 27.3% < 40%，自动静默归档。', 'archived_low', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (417, '2026-03-09 21:16:56', '/static/fire_1_20260309_211655.jpg', 0.669873, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险
处置建议: 立即疏散人员，增派消防力量，防止火势蔓延。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (418, '2026-03-09 21:17:06', '/static/fire_1_20260309_211705.jpg', 0.402638, '东区瞭望塔', '[风险级别:高风险] 风险级别: 高风险 
处置建议: 紧急部署消防力量，迅速灭火，确保人员安全。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (419, '2026-03-09 21:17:16', '/static/fire_1_20260309_211715.jpg', 0.92628, '东区瞭望塔', '[风险级别:高风险] YOLO置信度 92.6% > 80%，直接判定高风险并进入人工处置。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (420, '2026-03-09 21:17:26', '/static/fire_1_20260309_211725.jpg', 0.271033, '东区瞭望塔', '[风险级别:低风险] YOLO置信度 27.1% < 40%，自动静默归档。', 'archived_low', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (421, '2026-03-09 21:20:32', '/static/fire_7_20260309_212031.jpg', 0.625679, '中区观测点A', '[风险级别:高风险] 风险级别: 高风险
处置建议: 立即组织灭火力量，疏散周边群众。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (422, '2026-03-09 21:20:42', '/static/fire_7_20260309_212041.jpg', 0.811226, '中区观测点A', '[风险级别:高风险] YOLO置信度 81.1% > 80%，直接判定高风险并进入人工处置。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (423, '2026-03-09 21:38:39', '/static/fire_10_20260309_213838.jpg', 0.625679, '?????', '[风险级别:高风险] 风险级别: 高风险
处置建议: 组织力量迅速灭火，疏散周边居民。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (424, '2026-03-09 21:38:39', '/static/fire_8_20260309_213838.jpg', 0.625679, '?????', '[风险级别:高风险] 风险级别: 高风险
处置建议: 紧急疏散，迅速灭火，实施隔离。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (425, '2026-03-09 21:38:39', '/static/fire_9_20260309_213839.jpg', 0.625679, '??????', '[风险级别:高风险] 风险级别: 高风险
处置建议: 派出专业队伍紧急扑救，增派人手监控火势，实施隔离带。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (426, '2026-03-09 21:38:41', '/static/fire_12_20260309_213840.jpg', 0.709631, '????B', '[风险级别:高风险] 风险级别: 高风险
处置建议: 紧急疏散人员，迅速灭火，防止蔓延。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (427, '2026-03-09 21:38:47', '/static/fire_10_20260309_213847.jpg', 0.723869, '?????', '[风险级别:高风险] 风险级别: 高风险
处置建议: 加强火源管理，及时扑灭火源。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (428, '2026-03-09 21:38:48', '/static/fire_9_20260309_213847.jpg', 0.723869, '??????', '[风险级别:高风险] 风险级别: 高风险
处置建议: 紧急疏散森林居民，加强灭火力量，防止火势蔓延。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (429, '2026-03-09 21:38:48', '/static/fire_8_20260309_213847.jpg', 0.786086, '?????', '[风险级别:高风险] 风险级别: 高风险
处置建议: 立即疏散周围居民，增派消防力量。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (430, '2026-03-09 21:38:51', '/static/fire_12_20260309_213850.jpg', 0.756155, '????B', '[风险级别:高风险] 风险级别: 高风险
处置建议: 紧急疏散，迅速灭火，加强监测。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (431, '2026-03-09 21:40:44', '/static/fire_9_20260309_214044.jpg', 0.401002, '??????', '[风险级别:高风险] 风险级别: 高风险
处置建议: 快速疏散人员，设置消防设备，通知消防部门。', 'pending_verify', NULL);
INSERT INTO `alert` (`id`, `timestamp`, `image_path`, `yolo_confidence`, `camera_name`, `llm_result`, `status`, `remark`) VALUES (432, '2026-03-09 21:40:54', '/static/fire_9_20260309_214054.jpg', 0.696562, '??????', '[风险级别:高风险] 风险级别: 高风险  
处置建议: 紧急调动消防资源，全面扑灭。', 'pending_verify', NULL);

-- Table: announcement
DROP TABLE IF EXISTS `announcement`;
CREATE TABLE `announcement` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `category` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_published` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `announcement` (`id`, `title`, `content`, `category`, `is_published`, `created_at`) VALUES (1, '系统上线通知', '本系统已于 2026 年 3 月正式上线，请各岗位人员及时熟悉操作流程。', 'notice', 1, '2026-03-05 14:19:50');
INSERT INTO `announcement` (`id`, `title`, `content`, `category`, `is_published`, `created_at`) VALUES (2, '值班人员注意事项', '1. 每小时至少检查一次监控大屏
2. 发现告警后立即核实
3. 确认火灾需 5 分钟内上报
4. 交接班必须填写交接日志', 'sop', 1, '2026-03-05 14:19:50');
INSERT INTO `announcement` (`id`, `title`, `content`, `category`, `is_published`, `created_at`) VALUES (3, '误报处理流程', '1. 点击"标记为误报"
2. 在备注栏填写误报原因（如夕阳反光、工业排烟等）
3. 主管定期审核误报率', 'sop', 1, '2026-03-05 14:19:50');
INSERT INTO `announcement` (`id`, `title`, `content`, `category`, `is_published`, `created_at`) VALUES (4, 'notice test', 'notice test
notice test', 'notice', 1, '2026-03-05 14:26:06');

-- Table: camera
DROP TABLE IF EXISTS `camera`;
CREATE TABLE `camera` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `rtsp_url` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `location` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime NOT NULL,
  `enable_ai` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id`),
  KEY `ix_camera_name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `camera` (`id`, `name`, `rtsp_url`, `location`, `status`, `created_at`, `enable_ai`) VALUES (1, '东区瞭望塔', 'rtsp://192.168.1.101:554/stream', '东区山顶', 'online', '2026-03-05 14:09:57', 0);
INSERT INTO `camera` (`id`, `name`, `rtsp_url`, `location`, `status`, `created_at`, `enable_ai`) VALUES (2, '西区林道入口', 'rtsp://192.168.1.102:554/stream', '西区入口处', 'offline', '2026-03-05 14:09:57', 0);
INSERT INTO `camera` (`id`, `name`, `rtsp_url`, `location`, `status`, `created_at`, `enable_ai`) VALUES (3, '北区防火带', 'rtsp://192.168.1.103:554/stream', '北区防火隔离带', 'offline', '2026-03-05 14:09:57', 0);
INSERT INTO `camera` (`id`, `name`, `rtsp_url`, `location`, `status`, `created_at`, `enable_ai`) VALUES (4, '南区管理站', 'rtsp://192.168.1.104:554/stream', '南区管理站楼顶', 'offline', '2026-03-05 14:09:57', 0);
INSERT INTO `camera` (`id`, `name`, `rtsp_url`, `location`, `status`, `created_at`, `enable_ai`) VALUES (6, '一号公寓北', 'rtsp://192.168.1.102:554/stream', '一号公寓北侧', 'offline', '2026-03-07 14:52:27', 0);
INSERT INTO `camera` (`id`, `name`, `rtsp_url`, `location`, `status`, `created_at`, `enable_ai`) VALUES (7, '中区观测点A', 'rtsp://192.168.10.105:554/stream1', '中区高点A', 'offline', '2026-03-09 13:20:23', 0);
INSERT INTO `camera` (`id`, `name`, `rtsp_url`, `location`, `status`, `created_at`, `enable_ai`) VALUES (8, '?????', 'rtsp://192.168.20.201:554/live', '??????', 'offline', '2026-03-09 13:30:45', 0);
INSERT INTO `camera` (`id`, `name`, `rtsp_url`, `location`, `status`, `created_at`, `enable_ai`) VALUES (9, '??????', 'rtsp://192.168.20.202:554/live', '??????', 'online', '2026-03-09 13:30:45', 0);
INSERT INTO `camera` (`id`, `name`, `rtsp_url`, `location`, `status`, `created_at`, `enable_ai`) VALUES (10, '?????', 'rtsp://192.168.20.203:554/live', '??????', 'offline', '2026-03-09 13:30:45', 0);
INSERT INTO `camera` (`id`, `name`, `rtsp_url`, `location`, `status`, `created_at`, `enable_ai`) VALUES (11, '???????2?', 'rtsp://192.168.20.204:554/live', '?????2??', 'offline', '2026-03-09 13:30:45', 0);
INSERT INTO `camera` (`id`, `name`, `rtsp_url`, `location`, `status`, `created_at`, `enable_ai`) VALUES (12, '????B', 'rtsp://192.168.20.205:554/live', '??????B', 'offline', '2026-03-09 13:30:45', 0);

-- Table: cameralog
DROP TABLE IF EXISTS `cameralog`;
CREATE TABLE `cameralog` (
  `id` int NOT NULL AUTO_INCREMENT,
  `camera_id` int NOT NULL,
  `event` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `timestamp` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `camera_id` (`camera_id`),
  CONSTRAINT `cameralog_ibfk_1` FOREIGN KEY (`camera_id`) REFERENCES `camera` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `cameralog` (`id`, `camera_id`, `event`, `timestamp`) VALUES (1, 1, '设备上线', '2026-03-03 08:09:57');
INSERT INTO `cameralog` (`id`, `camera_id`, `event`, `timestamp`) VALUES (2, 1, '信号弱', '2026-03-03 03:09:57');
INSERT INTO `cameralog` (`id`, `camera_id`, `event`, `timestamp`) VALUES (3, 1, '信号弱', '2026-03-03 02:09:57');
INSERT INTO `cameralog` (`id`, `camera_id`, `event`, `timestamp`) VALUES (4, 2, '设备恢复', '2026-03-05 09:09:57');
INSERT INTO `cameralog` (`id`, `camera_id`, `event`, `timestamp`) VALUES (5, 2, '设备掉线', '2026-03-04 05:09:57');
INSERT INTO `cameralog` (`id`, `camera_id`, `event`, `timestamp`) VALUES (6, 2, '信号弱', '2026-03-02 21:09:57');
INSERT INTO `cameralog` (`id`, `camera_id`, `event`, `timestamp`) VALUES (7, 3, '设备恢复', '2026-03-02 20:09:57');
INSERT INTO `cameralog` (`id`, `camera_id`, `event`, `timestamp`) VALUES (8, 3, '信号弱', '2026-03-05 06:09:57');
INSERT INTO `cameralog` (`id`, `camera_id`, `event`, `timestamp`) VALUES (9, 3, '设备掉线', '2026-03-04 08:09:57');
INSERT INTO `cameralog` (`id`, `camera_id`, `event`, `timestamp`) VALUES (10, 4, '设备上线', '2026-03-04 17:09:57');
INSERT INTO `cameralog` (`id`, `camera_id`, `event`, `timestamp`) VALUES (11, 4, '设备上线', '2026-03-04 22:09:57');
INSERT INTO `cameralog` (`id`, `camera_id`, `event`, `timestamp`) VALUES (12, 4, '信号弱', '2026-03-04 02:09:57');

-- Table: captureconfig
DROP TABLE IF EXISTS `captureconfig`;
CREATE TABLE `captureconfig` (
  `id` int NOT NULL AUTO_INCREMENT,
  `camera_id` int DEFAULT NULL,
  `enable_capture` tinyint(1) NOT NULL,
  `capture_interval` int NOT NULL,
  `save_original` tinyint(1) NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `captureconfig` (`id`, `camera_id`, `enable_capture`, `capture_interval`, `save_original`, `updated_at`) VALUES (1, 1, 1, 5, 1, '2026-03-05 14:09:57');
INSERT INTO `captureconfig` (`id`, `camera_id`, `enable_capture`, `capture_interval`, `save_original`, `updated_at`) VALUES (2, 2, 1, 5, 1, '2026-03-05 14:09:57');
INSERT INTO `captureconfig` (`id`, `camera_id`, `enable_capture`, `capture_interval`, `save_original`, `updated_at`) VALUES (3, 3, 1, 3, 1, '2026-03-05 14:09:57');
INSERT INTO `captureconfig` (`id`, `camera_id`, `enable_capture`, `capture_interval`, `save_original`, `updated_at`) VALUES (4, 4, 1, 3, 1, '2026-03-05 14:09:57');

-- Table: shiftlog
DROP TABLE IF EXISTS `shiftlog`;
CREATE TABLE `shiftlog` (
  `id` int NOT NULL AUTO_INCREMENT,
  `operator` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `shift_time` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `shiftlog` (`id`, `operator`, `shift_time`, `content`, `created_at`) VALUES (1, '张三', '2026-03-05 08:00 - 16:00', '白班正常巡检，无异常。', '2026-03-05 14:09:57');
INSERT INTO `shiftlog` (`id`, `operator`, `shift_time`, `content`, `created_at`) VALUES (2, '李四', '2026-03-05 16:00 - 00:00', '晚班接班，东区有疑似烟雾，已排查为村民烧秸秆。', '2026-03-05 14:09:57');
INSERT INTO `shiftlog` (`id`, `operator`, `shift_time`, `content`, `created_at`) VALUES (3, '王五', '2026-03-04 00:00 - 08:00', '夜班正常，所有设备运行稳定。', '2026-03-05 14:09:57');

-- Table: systemconfig
DROP TABLE IF EXISTS `systemconfig`;
CREATE TABLE `systemconfig` (
  `id` int NOT NULL AUTO_INCREMENT,
  `key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `label` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `group` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_systemconfig_key` (`key`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `systemconfig` (`id`, `key`, `value`, `label`, `group`, `updated_at`) VALUES (2, 'yolo_model_path', 'best.pt', 'YOLO 模型文件路径', 'ai', '2026-03-05 14:19:50');
INSERT INTO `systemconfig` (`id`, `key`, `value`, `label`, `group`, `updated_at`) VALUES (4, 'llm_api_url', 'https://api.siliconflow.cn/v1/chat/completions', '大模型 API 地址', 'llm', '2026-03-06 16:33:19');
INSERT INTO `systemconfig` (`id`, `key`, `value`, `label`, `group`, `updated_at`) VALUES (5, 'llm_api_key', 'sk-qolyfmztivypzaztxpemrowewutlsykuelzwszuoweoztpdx', '大模型 API Key', 'llm', '2026-03-06 16:34:20');
INSERT INTO `systemconfig` (`id`, `key`, `value`, `label`, `group`, `updated_at`) VALUES (6, 'llm_model', 'Pro/Qwen/Qwen2.5-VL-7B-Instruct', '大模型名称', 'llm', '2026-03-07 09:01:33');
INSERT INTO `systemconfig` (`id`, `key`, `value`, `label`, `group`, `updated_at`) VALUES (7, 'system_name', '森林火灾预警系统', '系统名称', 'general', '2026-03-07 13:29:46');
INSERT INTO `systemconfig` (`id`, `key`, `value`, `label`, `group`, `updated_at`) VALUES (8, 'alert_sound', 'false', '告警声音提醒', 'general', '2026-03-09 13:49:16');
INSERT INTO `systemconfig` (`id`, `key`, `value`, `label`, `group`, `updated_at`) VALUES (9, 'yolo_interval', '3', 'YOLO 检测间隔 (秒)，非检测帧跳过推理', 'ai', '2026-03-08 16:30:23');
INSERT INTO `systemconfig` (`id`, `key`, `value`, `label`, `group`, `updated_at`) VALUES (10, 'yolo_high_threshold', '0.8', '高置信度阈值，≥此值直接判定火灾', 'ai', '2026-03-08 15:15:21');
INSERT INTO `systemconfig` (`id`, `key`, `value`, `label`, `group`, `updated_at`) VALUES (11, 'yolo_low_threshold', '0.4', '低置信度阈值，低于此值忽略', 'ai', '2026-03-08 16:30:20');
INSERT INTO `systemconfig` (`id`, `key`, `value`, `label`, `group`, `updated_at`) VALUES (12, 'alert_cooldown', '10', '告警冷却时间 (秒)，期间不再重复检测', 'ai', '2026-03-08 15:15:23');
INSERT INTO `systemconfig` (`id`, `key`, `value`, `label`, `group`, `updated_at`) VALUES (13, 'yolo_infer_scale', '0.7', '推理前缩放比例（0.2-1.0）', 'ai', '2026-03-08 15:15:24');
INSERT INTO `systemconfig` (`id`, `key`, `value`, `label`, `group`, `updated_at`) VALUES (14, 'fire_dispatch_phone', '119', '联动消防电话', 'general', '2026-03-08 16:29:30');

-- Table: systemlog
DROP TABLE IF EXISTS `systemlog`;
CREATE TABLE `systemlog` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `action` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `detail` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ip` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `timestamp` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `systemlog` (`id`, `user`, `action`, `detail`, `ip`, `timestamp`) VALUES (1, 'admin', '登录系统', '管理员登录', '127.0.0.1', '2026-03-03 15:19:50');
INSERT INTO `systemlog` (`id`, `user`, `action`, `detail`, `ip`, `timestamp`) VALUES (2, 'admin', '创建用户', '新增用户 operator', '127.0.0.1', '2026-03-04 14:19:50');
INSERT INTO `systemlog` (`id`, `user`, `action`, `detail`, `ip`, `timestamp`) VALUES (3, 'operator', '处理告警', '告警ID #3 标记为误报', '192.168.1.50', '2026-03-04 12:19:50');
INSERT INTO `systemlog` (`id`, `user`, `action`, `detail`, `ip`, `timestamp`) VALUES (4, 'manager', '查看统计', '访问统计看板', '192.168.1.60', '2026-03-04 14:19:50');
INSERT INTO `systemlog` (`id`, `user`, `action`, `detail`, `ip`, `timestamp`) VALUES (5, 'admin', '修改配置', 'YOLO 置信度阈值调整为 0.7', '127.0.0.1', '2026-03-05 09:19:50');
INSERT INTO `systemlog` (`id`, `user`, `action`, `detail`, `ip`, `timestamp`) VALUES (6, 'operator', '登录系统', '操作员登录', '192.168.1.50', '2026-03-04 12:19:50');

-- Table: user
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `hashed_password` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `role` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_user_username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `user` (`id`, `username`, `hashed_password`, `role`, `is_active`, `created_at`) VALUES (1, 'admin', '$2b$12$vCNtk4ku/vRpR1EGXAM76.EufJexge1qO7vVFkZSrzVh5EJq9GVEq', 'admin', 1, '2026-03-05 13:34:03');
INSERT INTO `user` (`id`, `username`, `hashed_password`, `role`, `is_active`, `created_at`) VALUES (2, 'manager', '$2b$12$qq2jiww/YuXiW3Lz/AbhFOvp8/t5M6QcFdBwk.dMUs9zor863KQWy', 'supervisor', 1, '2026-03-05 13:34:03');
INSERT INTO `user` (`id`, `username`, `hashed_password`, `role`, `is_active`, `created_at`) VALUES (3, 'operator', '$2b$12$qLJZBm8FR660JSta9Mggd.mv53aheQjWXGz7va6qPsZNvem5pBwy2', 'operator', 1, '2026-03-05 13:34:03');
INSERT INTO `user` (`id`, `username`, `hashed_password`, `role`, `is_active`, `created_at`) VALUES (4, 'operator2', '$2b$12$TUUtqIQLIfN7RaYpiNRqc.tdET4nXXsdMScR.uPLFuTgMRbnGpspW', 'operator', 1, '2026-03-08 16:32:01');
