"""Default message templates for CyberHerd Messaging.

These values mirror the structure used by the external middleware `messages.py`.
They are provided as convenient seed data so users can start quickly.
"""

CYBER_HERD_JOIN = {
    "0": {
        "content": "{name} has joined the ⚡ CyberHerd ⚡. {thanks_part} The feeder will activate in {difference} sats.\n\n https://lightning-goats.com\n\n",
        "reply_relay": "https://relay.damus.io"
    },
    "1": {
        "content": "Welcome, {name}. {thanks_part} The ⚡ CyberHerd ⚡ grows. {difference} sats are required for the next feeding cycle.\n\n https://lightning-goats.com\n\n",
        "reply_relay": "https://nostr-pub.wellorder.net"
    },
}

THANK_YOU_VARIATIONS = {
    "0": {"content": "Thank you for the contribution of {new_amount} sats.", "reply_relay": "https://relay.snort.social"},
    "1": {"content": "Your {new_amount} sat contribution has been received and supports the herd.", "reply_relay": "https://relay.snort.social"},
}

VARIATIONS = {
    "0": "{difference} sats are required for feeder activation.",
    "1": "The next feeding cycle will begin in {difference} sats.",
    "2": "Awaiting a remaining {difference} sats to trigger the feeder.",
    "3": "{difference} sats needed before the goats receive their treats.",
    "4": "The feeder is {difference} sats away from activation.",
    "5": "The feeding protocol will initiate after {difference} more sats.",
    "6": "The system requires an additional {difference} sats to dispense treats.",
    "7": "The feeder activation is pending {difference} more sats.",
    "8": "{difference} sats remaining until the next scheduled feeding.",
    "9": "Please note: {difference} more sats are needed for the next feeding.",
    "10": "The feeder will dispense treats once {difference} more sats are contributed."
}

GOAT_NAMES_DICT = {
    "Dexter": [
        "nostr:nprofile1qqsw4zlzyfx43mc88psnlse8sywpfl45kuap9dy05yzkepkvu6ca5wg7qyak5",
        "ea8be2224d58ef0738613fc327811c14feb4b73a12b48fa1056c86cce6b1da39"
    ],
    "Rowan": [
        "nostr:nprofile1qqs2w94r0fs29gepzfn5zuaupn969gu3fstj3gq8kvw3cvx9fnxmaugwur22r",
        "a716a37a60a2a32112674173bc0ccba2a3914c1728a007b31d1c30c54ccdbef1"
    ],
    "Nova": [
        "nostr:nprofile1qqsrzy7clymq5xwcfhh0dfz6zfe7h63k8r0j8yr49mxu6as4yv2084s0vf035",
        "3113d8f9360a19d84deef6a45a1273ebea3638df2390752ecdcd76152314f3d6"
    ],
    "Cosmo": [
        "nostr:nprofile1qqsq6n8u7dzrnhhy7xy78k2ee7e4wxlgrkm5g2rgjl3napr9q54n4ncvkqcsj",
        "0d4cfcf34439dee4f189e3d959cfb3571be81db744286897e33e8465052b3acf"
    ],
    "Newton": [
        "nostr:nprofile1qqszdsnpyzwhjcqads3hwfywt5jfmy85jvx8yup06yq0klrh93ldjxc26lmyx",
        "26c261209d79601d6c2377248e5d249d90f4930c72702fd100fb7c772c7ed91b"
    ]
}

CYBER_HERD_TREATS = {
    "0": "{name} has received a reward of {new_amount} sats from the ⚡ CyberHerd ⚡ distribution.\n\n https://lightning-goats.com\n\n",
    "1": "A distribution of {new_amount} sats has been sent to {name} as part of their ⚡ CyberHerd ⚡ membership.\n\n https://lightning-goats.com\n\n",
}

HEADBUTT_SUCCESS = {
    "0": {"content": "⚡headbutt⚡: A new member has joined the ⚡ CyberHerd ⚡. {attacker_name} ({attacker_amount} sats) has displaced {victim_name} ({victim_amount} sats).\n\n https://lightning-goats.com\n\n", "reply_relay": "https://relay.damus.io"},
    "1": {"content": "⚡headbutt⚡: The ⚡ CyberHerd ⚡ roster has been updated. {attacker_name} ({attacker_amount} sats) has taken the position previously held by {victim_name} ({victim_amount} sats).\n\n https://lightning-goats.com\n\n", "reply_relay": "https://relay.damus.io"},
    "2": {"content": "⚡headbutt⚡: Membership change: {attacker_name} has entered the ⚡ CyberHerd ⚡ with a contribution of {attacker_amount} sats, displacing {victim_name} ({victim_amount} sats).\n\n https://lightning-goats.com\n\n", "reply_relay": "https://nostr-pub.wellorder.net"},
    "3": {"content": "⚡headbutt⚡: A position in the ⚡ CyberHerd ⚡ has been filled by {attacker_name} ({attacker_amount} sats). The previous member, {victim_name} ({victim_amount} sats), has been removed.\n\n https://lightning-goats.com\n\n", "reply_relay": "https://nostr-pub.wellorder.net"},
    "4": {"content": "⚡headbutt⚡: Update: {attacker_name} is now a member of the ⚡ CyberHerd ⚡ with a {attacker_amount} sat contribution, replacing {victim_name} ({victim_amount} sats).\n\n https://lightning-goats.com\n\n", "reply_relay": "https://relay.snort.social"}
}

HEADBUTT_FAILURE = {
    "0": "⚡headbutt⚡: The ⚡ CyberHerd ⚡ is currently at full capacity. To join, a contribution of {required_sats} sats is needed to displace the member with the lowest contribution, {victim_name}.\n\n https://lightning-goats.com\n\n",
    "1": "⚡headbutt⚡: The ⚡ CyberHerd ⚡ is at capacity. A contribution greater than {required_sats} sats will grant you {victim_name}'s position.\n\n https://lightning-goats.com\n\n",
    "2": "⚡headbutt⚡: The ⚡ CyberHerd ⚡ is full. To become a member, you must contribute more than the lowest member's amount of {required_sats} sats, currently held by {victim_name}.\n\n https://lightning-goats.com\n\n",
    "3": "⚡headbutt⚡: Membership in the ⚡ CyberHerd ⚡ is currently full. You can gain a spot by contributing at least {required_sats} sats, which will displace {victim_name}.\n\n https://lightning-goats.com\n\n",
    "4": "⚡headbutt⚡: There are no available spots in the ⚡ CyberHerd ⚡. A contribution of {required_sats} sats or more is required to take the place of {victim_name}.\n\n https://lightning-goats.com\n\n"
}

HEADBUTT_INFO = {
    "0": "⚡headbutt⚡: The ⚡ CyberHerd ⚡ is currently at full capacity. To join, a contribution of {required_sats} sats is needed to displace the member with the lowest contribution, {victim_name}.\n\n https://lightning-goats.com\n\n",
}

MEMBER_INCREASE = {
    "0": "{member_name} increased their contribution by {increase_amount} sats, bringing their total to {new_total} sats.\n\n https://lightning-goats.com\n\n",
    "1": "{member_name} has boosted their ⚡ CyberHerd ⚡ contribution by {increase_amount} sats, now totaling {new_total} sats.\n\n https://lightning-goats.com\n\n",
    "2": "Contribution update: {member_name} added {increase_amount} sats to their total of {new_total} sats in the ⚡ CyberHerd ⚡.\n\n https://lightning-goats.com\n\n",
    "3": "{member_name} has increased their stake in the ⚡ CyberHerd ⚡ by {increase_amount} sats, reaching a total of {new_total} sats.\n\n https://lightning-goats.com\n\n",
    "4": "⚡ CyberHerd ⚡ update: {member_name} has grown their contribution by {increase_amount} sats, now at {new_total} sats total.\n\n https://lightning-goats.com\n\n"
}

DAILY_RESET = {
    "0": "🔄 Daily CyberHerd reset completed. All member contributions have been reset to zero. New feeding cycle begins now!\n\n https://lightning-goats.com\n\n",
    "1": "🌅 Good morning! The CyberHerd has been reset for a new day. All contributions cleared and ready for fresh participation.\n\n https://lightning-goats.com\n\n",
    "2": "⚡ System reset: Daily CyberHerd cycle has begun. Previous contributions have been cleared. Welcome to participate!\n\n https://lightning-goats.com\n\n",
    "3": "🔄 CyberHerd daily reset executed. All member balances reset to zero. Time to start contributing again!\n\n https://lightning-goats.com\n\n",
    "4": "🌟 New day, new opportunities! CyberHerd has been reset and is ready for fresh contributions.\n\n https://lightning-goats.com\n\n"
}

FEEDER_TRIGGER = {
    "0": {"content": "🎉 Feeder activated! {new_amount} sats have triggered the feeding mechanism. {difference_message} Scientific fact: Goats, such as {goat_name}, have uniquely shaped rectangular pupils, which provide them a wide field of vision, aiding in predator detection.\n\n https://lightning-goats.com\n\n", "reply_relay": "https://relay.damus.io"},
    "1": {"content": "⚡ Feeder trigger reached! {new_amount} sats collected - dispensing treats to CyberHerd members. {difference_message} Fun fact: {goat_name} and other goats are incredibly agile climbers, capable of scaling steep terrain with ease.\n\n https://lightning-goats.com\n\n", "reply_relay": "https://relay.snort.social"},
    "2": {"content": "🎊 Feeding time! The CyberHerd has collected {new_amount} sats and the feeder has been activated. {difference_message} Did you know? {goat_name} represents the curious and intelligent nature of goats in general.\n\n https://lightning-goats.com\n\n", "reply_relay": "https://nostr-pub.wellorder.net"},
    "3": {"content": "🚀 Feeder activated with {new_amount} sats! CyberHerd members will receive their earned rewards. {difference_message} Interesting: Goats like {goat_name} have excellent memories and can recognize other goats and humans for years.\n\n https://lightning-goats.com\n\n", "reply_relay": "https://nostr-pub.wellorder.net"},
    "4": {"content": "⚡ CyberHerd feeding initiated! {new_amount} sats collected - treats being distributed now. {difference_message} Goat trivia: {goat_name} exemplifies how goats use their prehensile tongues to be selective eaters, often choosing the most nutritious parts of a plant.\n\n https://lightning-goats.com\n\n", "reply_relay": "https://relay.snort.social"}
}

FEEDING_REGULAR = {
    "0": "{display_name} received {new_amount} sats from CyberHerd distribution.\n\n https://lightning-goats.com\n\n",
    "1": "Regular feeding: {display_name} has been credited with {new_amount} sats.\n\n https://lightning-goats.com\n\n",
    "2": "⚡ CyberHerd payout: {new_amount} sats sent to {display_name}.\n\n https://lightning-goats.com\n\n",
    "3": "Distribution complete: {display_name} received {new_amount} sats from the herd.\n\n https://lightning-goats.com\n\n",
    "4": "Feeding reward: {new_amount} sats delivered to {display_name}.\n\n https://lightning-goats.com\n\n"
}

FEEDING_BONUS = {
    "0": "🎁 Bonus feeding! {display_name} received {new_amount} sats as a special reward.\n\n https://lightning-goats.com\n\n",
    "1": "⚡ Special bonus: {display_name} has been credited with {new_amount} sats.\n\n https://lightning-goats.com\n\n",
    "2": "🎊 Bonus distribution: {new_amount} sats sent to {display_name}.\n\n https://lightning-goats.com\n\n",
    "3": "Extra reward: {display_name} received {new_amount} sats bonus from CyberHerd.\n\n https://lightning-goats.com\n\n",
    "4": "🎉 Special feeding: {new_amount} sats bonus delivered to {display_name}.\n\n https://lightning-goats.com\n\n"
}

FEEDING_REMAINDER = {
    "0": "📦 Remainder distribution: {display_name} received {new_amount} sats from remaining funds.\n\n https://lightning-goats.com\n\n",
    "1": "Final payout: {display_name} has been credited with {new_amount} sats remainder.\n\n https://lightning-goats.com\n\n",
    "2": "⚡ Remainder funds: {new_amount} sats sent to {display_name}.\n\n https://lightning-goats.com\n\n",
    "3": "Leftover distribution: {display_name} received {new_amount} sats from remainder.\n\n https://lightning-goats.com\n\n",
    "4": "Final distribution: {new_amount} sats remainder delivered to {display_name}.\n\n https://lightning-goats.com\n\n"
}

FEEDING_FALLBACK = {
    "0": "🔄 Fallback distribution: {display_name} received {new_amount} sats via predefined wallet.\n\n https://lightning-goats.com\n\n",
    "1": "System fallback: {display_name} has been credited with {new_amount} sats.\n\n https://lightning-goats.com\n\n",
    "2": "⚡ Fallback payout: {new_amount} sats sent to {display_name}.\n\n https://lightning-goats.com\n\n",
    "3": "Predefined distribution: {display_name} received {new_amount} sats fallback.\n\n https://lightning-goats.com\n\n",
    "4": "System distribution: {new_amount} sats fallback delivered to {display_name}.\n\n https://lightning-goats.com\n\n"
}

INTERFACE_INFO = {
    "0": "🔧 System interface information: All systems operational. CyberHerd ready for contributions.\n\n https://lightning-goats.com\n\n",
    "1": "ℹ️ Interface status: CyberHerd system is online and accepting payments.\n\n https://lightning-goats.com\n\n",
    "2": "⚡ System check: All CyberHerd interfaces functioning normally.\n\n https://lightning-goats.com\n\n",
    "3": "🔄 Status update: CyberHerd interface is active and ready.\n\n https://lightning-goats.com\n\n",
    "4": "📊 System info: CyberHerd operational with all interfaces online.\n\n https://lightning-goats.com\n\n"
}

SATS_RECEIVED = {
    "0": "💰 Payment received: {new_amount} sats added to CyberHerd. {difference_message} Scientific fact: Goats, such as {goat_name}, have uniquely shaped rectangular pupils, which provide them a wide field of vision, aiding in predator detection.\n\n https://lightning-goats.com\n\n",
    "1": "⚡ Contribution confirmed: {new_amount} sats received. {difference_message} Fun fact: {goat_name} and other goats are incredibly agile climbers, capable of scaling steep terrain with ease.\n\n https://lightning-goats.com\n\n",
    "2": "💎 Payment processed: {new_amount} sats contributed. {difference_message} Did you know? {goat_name} represents the curious and intelligent nature of goats in general.\n\n https://lightning-goats.com\n\n",
    "3": "🔥 Sats received: {new_amount} added to the pot. {difference_message} Interesting: Goats like {goat_name} have excellent memories and can recognize other goats and humans for years.\n\n https://lightning-goats.com\n\n",
    "4": "⚡ CyberHerd grows: {new_amount} sats received. {difference_message} Goat trivia: {goat_name} exemplifies how goats use their prehensile tongues to selectively eat the most nutritious plants.\n\n https://lightning-goats.com\n\n"
}

# Category name -> dict[key -> template]
from typing import Any

SEED_DEFAULTS: dict[str, dict[str, Any]] = {
    "cyber_herd_join": CYBER_HERD_JOIN,
    "thank_you_variations": THANK_YOU_VARIATIONS,
    "variations": VARIATIONS,
    "goat_names_dict": GOAT_NAMES_DICT,
    "cyber_herd_treats": CYBER_HERD_TREATS,
    "headbutt_success": HEADBUTT_SUCCESS,
    "headbutt_failure": HEADBUTT_FAILURE,
    "headbutt_info": HEADBUTT_INFO,
    "member_increase": MEMBER_INCREASE,
    "daily_reset_dict": DAILY_RESET,
    "feeder_trigger_dict": FEEDER_TRIGGER,
    "feeding_regular_dict": FEEDING_REGULAR,
    "feeding_bonus_dict": FEEDING_BONUS,
    "feeding_remainder_dict": FEEDING_REMAINDER,
    "feeding_fallback_dict": FEEDING_FALLBACK,
    "interface_info_dict": INTERFACE_INFO,
    "sats_received_dict": SATS_RECEIVED,
}
