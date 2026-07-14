/**
 * 弹幕消息 DTO 类型定义 & 解析器
 * 基于 WssBarrageServer WebSocket 实际输出
 */

// ── 消息类型枚举 ──
const MsgType = Object.freeze({
  BARRAGE:    1,  // 普通弹幕
  LIKE:       2,  // 点赞
  ENTER:      3,  // 进入直播间
  FOLLOW:     4,  // 关注
  GIFT:       5,  // 礼物
  STATS:      6,  // 直播间统计
  FANS_CLUB:  7,  // 粉丝团
  SHARE:      8,  // 分享
  LIVE_END:   9,  // 下播
});

const MsgTypeName = Object.freeze({
  1: '弹幕', 2: '点赞', 3: '进入', 4: '关注',
  5: '礼物', 6: '统计', 7: '粉丝团', 8: '分享', 9: '下播',
});

// ── 用户信息 ──
/**
 * @typedef {Object} FansClub
 * @property {string} ClubName
 * @property {number} Level
 */

/**
 * @typedef {Object} User
 * @property {number} Id
 * @property {string} Nickname
 * @property {string} DisplayId
 * @property {number} ShortId
 * @property {number} Gender        // 0=未知 1=男 2=女
 * @property {number} Level
 * @property {number} PayLevel
 * @property {string} HeadImgUrl
 * @property {string} SecUid
 * @property {number} FollowerCount
 * @property {number} FollowingCount
 * @property {number} FollowStatus
 * @property {boolean} IsAdmin
 * @property {boolean} IsAnchor
 * @property {FansClub} FansClub
 */

/**
 * @typedef {Object} BarrageMsg
 * @property {number} Type          // = 1
 * @property {string} ProcessName   // "chrome"
 * @property {string} MsgId
 * @property {string} Content       // 弹幕文本
 * @property {string} RoomId
 * @property {string} WebRoomId
 * @property {string} Appid
 * @property {User} User
 */

/**
 * @typedef {Object} EnterMsg
 * @property {number} Type          // = 3
 * @property {string} ProcessName
 * @property {string} MsgId
 * @property {string} Content
 * @property {string} RoomId
 * @property {string} WebRoomId
 * @property {string} Appid
 * @property {number} CurrentCount  // 当前在线人数
 * @property {User} User
 */

/**
 * @typedef {Object} StatsMsg
 * @property {number} Type          // = 6
 * @property {string} ProcessName
 * @property {string} MsgId
 * @property {string} Content
 * @property {string} RoomId
 * @property {string} WebRoomId
 * @property {string} Appid
 * @property {number} OnlineUserCount
 * @property {number} TotalUserCount
 */

/**
 * 解析弹幕 WebSocket 原始消息为类型化对象
 * @param {string|object} raw - WebSocket 收到的原始数据
 * @returns {BarrageMsg|EnterMsg|StatsMsg|null}
 */
function parseBarrage(raw) {
  let outer;
  if (typeof raw === 'string') {
    try { outer = JSON.parse(raw); } catch { return null; }
  } else {
    outer = raw;
  }

  if (!outer || !outer.Type) return null;

  // 解析内层 Data 字符串
  let inner;
  if (typeof outer.Data === 'string') {
    try { inner = JSON.parse(outer.Data); } catch { inner = {}; }
  } else {
    inner = outer.Data || {};
  }

  // 构建类型化消息：展开内层字段 + 保留外层 Type / ProcessName
  const msg = {
    Type:        outer.Type,
    ProcessName: outer.ProcessName || '',
    MsgId:       inner.MsgId ?? '',
    Content:     inner.Content ?? '',
    RoomId:      inner.RoomId ?? '',
    WebRoomId:   inner.WebRoomId ?? '',
    Appid:       inner.Appid ?? '',
    User:        inner.User || null,
  };

  // 按类型附加特有字段
  switch (outer.Type) {
    case MsgType.ENTER:
      msg.CurrentCount = inner.CurrentCount ?? 0;
      break;
    case MsgType.STATS:
      msg.OnlineUserCount = inner.OnlineUserCount ?? 0;
      msg.TotalUserCount  = inner.TotalUserCount ?? 0;
      break;
    case MsgType.LIKE:
      msg.LikeCount = inner.LikeCount ?? inner.Count ?? 0;
      break;
    case MsgType.GIFT:
      msg.GiftName  = inner.GiftName ?? '';
      msg.GiftCount = inner.GiftCount ?? 1;
      break;
  }

  return msg;
}

// ── 导出 ──
module.exports = {
  MsgType,
  MsgTypeName,
  parseBarrage,
};
