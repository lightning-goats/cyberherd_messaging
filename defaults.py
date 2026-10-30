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

# Brief outcome-only failure lines. The actionable guidance ("how to actually
# headbutt") lives in the CALL_TO_ACTION category and is appended at render time.
HEADBUTT_FAILURE = {
    "0": "⚡headbutt⚡: The ⚡ CyberHerd ⚡ is full and {attacker_name}'s {attacker_amount} sats didn't top {victim_name}.",
    "1": "⚡headbutt⚡: No luck this time, {attacker_name} — {attacker_amount} sats wasn't enough to unseat {victim_name}.",
    "2": "⚡headbutt⚡: The herd is at capacity and {attacker_name}'s {attacker_amount} sats fell short of {victim_name}.",
    "3": "⚡headbutt⚡: {attacker_name}'s {attacker_amount} sats didn't clear {victim_name}'s spot — the herd stays full.",
    "4": "⚡headbutt⚡: So close, {attacker_name}! {attacker_amount} sats didn't overtake {victim_name}."
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

# Rejection when a free spot exists but the contribution is below the join
# minimum (no member is displaced — must not use "displace" wording).
# Brief outcome-only lines; the CALL_TO_ACTION category supplies the next step.
JOIN_BELOW_MINIMUM = {
    "0": "⚡ CyberHerd ⚡: A spot is open, but {name}'s {attacker_amount} sats is under the {required_sats} sat minimum to join.",
    "1": "⚡ CyberHerd ⚡: Almost, {name}! {attacker_amount} sats is just shy of the {required_sats} sats needed to join.",
    "2": "⚡ CyberHerd ⚡: {name} sent {attacker_amount} sats — the open spot needs at least {required_sats} sats.",
    "3": "⚡ CyberHerd ⚡: So close, {name}! {attacker_amount} sats falls {difference} short of the {required_sats} sat minimum.",
    "4": "⚡ CyberHerd ⚡: {name}'s {attacker_amount} sats didn't reach the {required_sats} sat join minimum this time.",
}

# Reusable "here's how to headbutt" snippets, keyed by the rejection category
# they attach to. render_and_publish_template appends the matching snippet to
# every rejection message so each one doubles as inline documentation.
CALL_TO_ACTION = {
    # Below-minimum zap while a spot is open: repost/react is free, or zap the minimum.
    "join_below_minimum": "👉 Repost or react to grab the open spot for free, or zap at least {required_sats} sats to join with a payout share.\n\n https://lightning-goats.com/leaderboard",
    # Zap didn't beat the lowest member (full herd of zappers).
    "headbutt_failure": "👉 Zap more than {required_sats} sats to displace {victim_name} and take their spot.\n\n https://lightning-goats.com/leaderboard",
    # Repost, but every member has zapped — nothing a repost can displace.
    "kind_6_headbutt_failure": "👉 Reposts can only bump repost/reaction members, and every seat here is held by a zapper. Zap more than {required_sats} sats to displace {victim_name}.\n\n https://lightning-goats.com/leaderboard",
    # Reaction on a full herd — reactions can never headbutt.
    "kind_7_headbutt_failure": "👉 Reactions can't headbutt. Repost to bump a repost/reaction member, or zap more than {required_sats} sats to displace {victim_name}.\n\n https://lightning-goats.com/leaderboard",
}

# A non-paying repost that displaces an existing (repost/reaction) member.
REPOST_DISPLACES = {
    "0": "⚡ CyberHerd ⚡: {name} amplified our signal and joined the herd, displacing {victim_name}. Thanks for sharing!\n\n https://lightning-goats.com/leaderboard\n\n",
    "1": "{name} reposted and took a spot in the ⚡ CyberHerd ⚡, bumping {victim_name}. Welcome aboard!\n\n https://lightning-goats.com/leaderboard\n\n",
    "2": "A repost from {name} makes room in the ⚡ CyberHerd ⚡ — {victim_name} has been displaced. Thank you for spreading the word!\n\n https://lightning-goats.com/leaderboard\n\n",
    "3": "The ⚡ CyberHerd ⚡ shifts: {name}'s repost earns them a place, displacing {victim_name}. Thanks for the boost!\n\n https://lightning-goats.com/leaderboard\n\n",
    "4": "{name} spread the word and edged out {victim_name} to join the ⚡ CyberHerd ⚡. We appreciate the amplification!\n\n https://lightning-goats.com/leaderboard\n\n",
}


# An EXISTING herd member reposts again (kind 6). They already belong to the
# herd, so this acknowledges the continued amplification rather than welcoming
# them as a new join.
EXISTING_MEMBER_REPOST = {
    "0": "{name} boosted the ⚡ CyberHerd ⚡ signal again. Thanks for the continued amplification!\n\n https://lightning-goats.com/leaderboard\n\n",
    "1": "Already riding with the ⚡ CyberHerd ⚡, {name} reposted once more. We appreciate you spreading the word!\n\n https://lightning-goats.com/leaderboard\n\n",
    "2": "Another repost from {name} — thanks for keeping the ⚡ CyberHerd ⚡ signal strong!\n\n https://lightning-goats.com/leaderboard\n\n",
    "3": "{name} is still amplifying the ⚡ CyberHerd ⚡. Thank you for the ongoing support!\n\n https://lightning-goats.com/leaderboard\n\n",
    "4": "The ⚡ CyberHerd ⚡ grows louder — {name} shared us again. Much appreciated!\n\n https://lightning-goats.com/leaderboard\n\n",
}


# An EXISTING herd member reacts again (kind 7). They already belong to the
# herd, so this thanks them for the continued support rather than welcoming
# them as a new join.
EXISTING_MEMBER_REACTION = {
    "0": "{name} sent another positive reaction to the ⚡ CyberHerd ⚡. Thanks for the continued support!\n\n https://lightning-goats.com/leaderboard\n\n",
    "1": "Already part of the ⚡ CyberHerd ⚡, {name} reacted again. We appreciate the encouragement!\n\n https://lightning-goats.com/leaderboard\n\n",
    "2": "More love from {name} for the ⚡ CyberHerd ⚡. Thank you for the positive feedback!\n\n https://lightning-goats.com/leaderboard\n\n",
    "3": "{name} keeps cheering on the ⚡ CyberHerd ⚡. Thanks for sticking with us!\n\n https://lightning-goats.com/leaderboard\n\n",
    "4": "A returning reaction from {name} — the ⚡ CyberHerd ⚡ appreciates the ongoing support!\n\n https://lightning-goats.com/leaderboard\n\n",
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
    "join_below_minimum": JOIN_BELOW_MINIMUM,
    "repost_displaces": REPOST_DISPLACES,
    "existing_member_repost": EXISTING_MEMBER_REPOST,
    "existing_member_reaction": EXISTING_MEMBER_REACTION,
    "call_to_action": CALL_TO_ACTION,
}


# Seed data only: durable messages are selected from the database, never from
# these dictionaries at publication time. Existing user rows are preserved.
SKIPPED_TREATS = {
    "0": "🐐 The big goats ate all the food this round, {name}! Your ⚡ CyberHerd ⚡ share was too small to send this time.",
    "1": "🐐 The big goats reached the treat bucket first, {name}! Your ⚡ CyberHerd ⚡ share was too small for a payment this round.",
    "2": "🐐 The big goats gobbled up this round's treats, {name}! Your ⚡ CyberHerd ⚡ slice was too small to send this time.",
    "3": "🐐 A few hungry goats beat you to the trough, {name}! Your ⚡ CyberHerd ⚡ share didn't reach the minimum needed to send a treat this round.",
    "4": "🐐 The big goats licked the bowl clean, {name}! Your ⚡ CyberHerd ⚡ share was too small to send in this distribution.",
    "5": "🐐 The biggest appetites got the bites this round, {name}! Your ⚡ CyberHerd ⚡ share was below the amount we could send as a treat.",
}
SKIPPED_TREATS = {
    key: content + "\n\n https://lightning-goats.com/leaderboard"
    for key, content in SKIPPED_TREATS.items()
}
SEED_DEFAULTS["cyber_herd_no_treats"] = SKIPPED_TREATS
SEED_DEFAULTS["cyber_herd_treats"] = {
    **CYBER_HERD_TREATS,
    "treat_0": "🍬 Treats delivered! {name} received {new_amount:g} sats from the ⚡ CyberHerd ⚡. A little something for your side of the trough!\n\n https://lightning-goats.com/leaderboard",
    "treat_1": "🐐 {name} got a bite of this round's treats: {new_amount:g} sats from the ⚡ CyberHerd ⚡ have landed in your wallet!\n\n https://lightning-goats.com/leaderboard",
    "treat_2": "⚡ CyberHerd ⚡ snack delivery for {name}! {new_amount:g} sats received — the big goats left you a bite this time. 🍬\n\n https://lightning-goats.com/leaderboard",
    "treat_3": "🐐 A share of the treat bucket made it to {name}! {new_amount:g} sats received from this ⚡ CyberHerd ⚡ distribution.\n\n https://lightning-goats.com/leaderboard",
    "treat_4": "🍬 Your place at the trough paid off, {name}! The ⚡ CyberHerd ⚡ sent {new_amount:g} sats your way. Thanks for running with the herd!\n\n https://lightning-goats.com/leaderboard",
    "treat_5": "🐐 The ⚡ CyberHerd ⚡ shared its snacks with {name}: {new_amount:g} sats delivered! Enjoy your bite of this round's treats.\n\n https://lightning-goats.com/leaderboard",
}
SEED_DEFAULTS["member_thread"] = {
    "0": "🐐 {name}, this is your CyberHerd member thread for this membership cycle. Treat updates will appear here.",
}
SEED_DEFAULTS["repost_hint"] = {
    "0": "A repost adds 3 points and could help you snag a bigger bite next round. 🍬",
    "1": "Want a bigger bite? Your first repost this cycle adds 3 points to your share. 🐐",
    "2": "A repost earns 3 points once this cycle and could help you reach the treat bucket next time. 🍬",
}
SEED_DEFAULTS["feeder_batch_summary"] = {
    "0": "This payment funds {feedings} feeder activation(s) and {payout_cycles} CyberHerd payout cycle(s).",
    "1": "On the menu: {feedings} feeder activation(s) and {payout_cycles} CyberHerd payout cycle(s) from this payment.",
}

# Specialised membership messages must also be editable database templates.
from .templates import messaging_templates as _specialised
for _category in ("kind_6_repost", "kind_7_reaction", "kind_6_headbutt_failure",
                  "kind_7_headbutt_failure", "zapper_displaces_kind_6", "zapper_displaces_kind_7"):
    SEED_DEFAULTS[_category] = getattr(_specialised, _category)

SEED_DEFAULTS["cyber_herd_treat_breakdown"] = {
    "0": "Your points this round:\n⚡ Zaps: {zap_sats} sats → {zap_points} points\n🔁 Repost: {repost_points} points\n❤️ Like: {like_points} points\nTotal: {total_points} points · Treat share: {share_percent}%",
}


CONTEXT_SUMMARIES = {
    "cyber_herd_current_score": {
        "0": "Your current points:\n⚡ Zaps: {zap_sats} sats → {zap_points} points\n🔁 Repost: {repost_points} points\n❤️ Like: {like_points} points\nTotal: {total_points} points · Current share: {share_percent}%\nShares can change before distribution.",
    },
    "cyber_herd_interaction_score": {
        "0": "This interaction added {earned_points} points.",
    },
    "cyber_herd_unadmitted_score": {
        "0": "This attempt did not earn membership points or a share. Qualifying likes and reposts can count after a later qualifying join.",
    },
    "cyber_herd_feeder_score": {
        "0": "Herd snapshot: {active_members} active members · {total_points} total points\nMember allocation: {member_allocation}%\nShares can change before distribution.",
    },
}
SEED_DEFAULTS.update(CONTEXT_SUMMARIES)


SEED_DEFAULTS["cyber_herd_zap_request"] = {
    "0": "🐐 CyberHerd treats for {name}: {new_amount:g} sats.",
}


STREAM_CHAT_NOTICES = {
    "feeder_command_accepted": {
        "0": "🐐 OpenHAB accepted a feeder command for this payment of {new_amount:g} sats. Physical food delivery has not been confirmed.",
        "1": "🐐 A feeder command was accepted by OpenHAB after {new_amount:g} sats arrived. This confirms the command, not physical food delivery.",
    },
    "feeder_batch_finished": {
        "0": "🐐 This payment's batch finished: {accepted_feedings} feeder command(s) accepted and {funding_cycles} CyberHerd funding transfer(s) completed. Physical food delivery is not confirmed; member treat notices follow settled payments.",
    },
    "feeder_outcome_uncertain": {
        "0": "🐐 The latest feeder command's outcome is uncertain. Automatic replay is paused for operator reconciliation. Before this request: {accepted_feedings} command(s) accepted and {funding_cycles} CyberHerd funding transfer(s) completed. Physical food delivery is not confirmed.",
    },
    'feeder_requests_paused': {
        '0': '🐐 The feeder is taking a little break. The goats will have to wait for their next round of snacks!',
        '1': '🐐 Snack time is on hold—the feeder is paused for now. Zaps can still arrive while the treat chute takes a breather.',
        '2': '🐐 A little pause at the trough! The feeder is resting, but you can still send zaps to the herd.',
        '3': '🐐 The goats are saving their appetites. The feeder is paused; we’ll let you know when snack time is back.',
        '4': '🐐 The treat chute is taking five. The feeder is paused for now, though zaps are still welcome.',
        '5': '🐐 Hold those hungry headbutts—the feeder is on a break! The next round of snacks will have to wait.',
    },
    'feeder_requests_enabled': {
        '0': '🐐 The feeder is back on the menu! Time to line up at the trough again.',
        '1': '🐐 Snack time is back! The feeder has resumed, and the goats are keeping an eye on the treat chute.',
        '2': '🐐 Break’s over at the trough. The feeder is ready for the next round of snacks!',
        '3': '🐐 The feeder’s little rest is over. Let’s get those hungry goats back in line!',
        '4': '🐐 Back to the snack business! The feeder is unpaused and the herd is all ears.',
        '5': '🐐 The wait at the trough is over—the feeder is back in action. Who’s ready for the next bite?',
    },
    "cyber_herd_invitation": {
        "0": "🐐 Want a place at the trough? Join the ⚡ CyberHerd ⚡ by supporting this stream. Qualifying zaps start at {minimum_sats} sats; a full herd may need a larger headbutt. Your first repost adds 3 points and first like adds 1, once per membership cycle. Zaps earn the most points and every settled zap counts. Members share {member_allocation}% of each treat distribution.\n\nhttps://lightning-goats.com/leaderboard",
        "1": "🐐 Run with the ⚡ CyberHerd ⚡! Zap this stream to build your score. Qualifying zaps start at {minimum_sats} sats; headbutts may need more. First repost: 3 points. First like: 1 point. Each counts once per membership cycle; every settled zap adds points. The member treat pool is {member_allocation}%.\n\nhttps://lightning-goats.com/leaderboard",
    },
    "cyber_herd_space_open": {
        "0": "Herd places: {active_members}/{max_members} filled · {spots_remaining} open. A first like or repost can join while a place is open.",
    },
    "cyber_herd_space_full": {
        "0": "Herd places: {active_members}/{max_members} filled. Qualifying zaps can challenge members; reposts can challenge eligible social-only members. Likes cannot headbutt.",
    },
}
SEED_DEFAULTS.update(STREAM_CHAT_NOTICES)


LEGACY_FEEDER_AVAILABILITY_TEMPLATES = {'feeder_requests_paused': {'0': '🐐 Feeder requests are paused by the operator. Feeding will wait until the pause is lifted.', '1': '🐐 The operator has paused feeder requests. The goats will have to wait for their next round of snacks.'}, 'feeder_requests_enabled': {'0': '🐐 The operator pause is lifted. Feeder requests are enabled again.', '1': '🐐 Feeder requests are back on the menu: the operator has lifted the pause.'}}


MESSAGE_VARIATIONS = {'cyber_herd_invitation': {'2': '🐐 There’s room for more enthusiasm at the trough! Support this '
                                'stream to build your ⚡ CyberHerd ⚡ score. Qualifying zaps start '
                                'at {minimum_sats} sats; a full herd may need more. Your first '
                                'repost adds 3 points, your first like adds 1, and every settled '
                                'zap adds points. The member treat pool is {member_allocation}%.\n'
                                '\n'
                                'https://lightning-goats.com/leaderboard',
                           '3': '🐐 The goats have their snacks. Want a share of the CyberHerd '
                                'treats? A minimum qualifying zap starts at {minimum_sats} sats, '
                                'with higher zaps earning more points. First repost: 3 points. '
                                'First like: 1 point, each once per membership cycle. Members '
                                'share {member_allocation}% of each treat distribution; a full '
                                'herd may need a bigger headbutt.\n'
                                '\n'
                                'https://lightning-goats.com/leaderboard',
                           '4': '🐐 Bring some spark to the ⚡ CyberHerd ⚡! Qualifying zaps to this '
                                'stream start at {minimum_sats} sats; headbutts can require more. '
                                'Every settled zap adds points, plus 3 for your first repost and 1 '
                                'for your first like this membership cycle. The herd’s members '
                                'share {member_allocation}% of each treat distribution.\n'
                                '\n'
                                'https://lightning-goats.com/leaderboard',
                           '5': '🐐 Fancy a place among the CyberHerd? Support this stream! '
                                'Qualifying zaps start at {minimum_sats} sats, and every settled '
                                'zap builds your score. Your first repost adds 3 points and first '
                                'like adds 1 per membership cycle. A full herd may call for a '
                                'larger headbutt. Members share a {member_allocation}% treat '
                                'pool.\n'
                                '\n'
                                'https://lightning-goats.com/leaderboard',
                           '6': '🐐 More cheering, more sharing! Build your ⚡ CyberHerd ⚡ score '
                                'with zaps to this stream. Qualifying zaps start at {minimum_sats} '
                                'sats; a full herd may need a larger headbutt. Add 3 points with '
                                'your first repost and 1 with your first like, once each per '
                                'membership cycle. Member treats come from {member_allocation}% of '
                                'each distribution.\n'
                                '\n'
                                'https://lightning-goats.com/leaderboard',
                           '7': '🐐 Pull up to the CyberHerd trough! Qualifying zaps start at '
                                '{minimum_sats} sats, with every settled zap adding points. Your '
                                'first repost earns 3 points and first like earns 1 this '
                                'membership cycle. A full herd can require a bigger headbutt to '
                                'join. The member treat bucket holds {member_allocation}% of each '
                                'distribution.\n'
                                '\n'
                                'https://lightning-goats.com/leaderboard'},
 'feeder_command_accepted': {'2': '🐐 A request is on its way to the trough: OpenHAB accepted a '
                                  'feeder command after {new_amount:g} sats arrived. Physical food '
                                  'delivery is not confirmed.',
                             '3': '🐐 {new_amount:g} sats brought a little excitement to the herd! '
                                  'OpenHAB accepted the feeder command; physical food delivery is '
                                  'not confirmed.',
                             '4': '🐐 The treat chute has a request waiting: OpenHAB accepted a '
                                  'feeder command for this {new_amount:g}-sat payment. That '
                                  'confirms the command, not physical food delivery.',
                             '5': '🐐 Heads up at the trough! After {new_amount:g} sats arrived, '
                                  'OpenHAB accepted a feeder command. Physical food delivery has '
                                  'not been confirmed.'},
 'feeder_batch_finished': {'1': '🐐 This round’s requests are wrapped up: {accepted_feedings} '
                                'feeder command(s) accepted and {funding_cycles} CyberHerd funding '
                                'transfer(s) completed. Physical food delivery is not confirmed; '
                                'member treat notices follow settled payments.',
                           '2': '🐐 Here’s the tally for this payment: {accepted_feedings} feeder '
                                'command(s) accepted, with {funding_cycles} CyberHerd funding '
                                'transfer(s) completed. Physical food delivery is not confirmed. '
                                'Members get their treat notices as payments settle.',
                           '3': '🐐 That’s this payment’s batch accounted for: {accepted_feedings} '
                                'feeder command(s) accepted and {funding_cycles} CyberHerd funding '
                                'transfer(s) completed. Physical food delivery is not confirmed; '
                                'individual treat notices follow settlement.',
                           '4': '🐐 The request tally is in! This payment finished with '
                                '{accepted_feedings} accepted feeder command(s) and '
                                '{funding_cycles} completed CyberHerd funding transfer(s). '
                                'Physical food delivery remains unconfirmed. Member treats are '
                                'announced when their payments settle.',
                           '5': '🐐 A quick count from the trough: {accepted_feedings} feeder '
                                'command(s) accepted; {funding_cycles} CyberHerd funding '
                                'transfer(s) completed for this payment. That does not confirm '
                                'physical food delivery. Member treat notices follow settled '
                                'payments.'},
 'feeder_outcome_uncertain': {'0': '🐐 The feeder’s latest request needs a check before we try '
                                   'again. So far: {accepted_feedings} command(s) accepted and '
                                   '{funding_cycles} CyberHerd funding transfer(s) completed. We '
                                   'can’t confirm what happened with the latest command or whether '
                                   'food was dispensed.',
                              '1': '🐐 A little uncertainty at the trough: we can’t confirm the '
                                   'latest feeder command, so it won’t be repeated automatically. '
                                   'Before it, {accepted_feedings} command(s) were accepted and '
                                   '{funding_cycles} CyberHerd funding transfer(s) completed. '
                                   'Physical food delivery is unconfirmed.',
                              '2': '🐐 The treat chute’s latest request needs a closer look. '
                                   'Automatic retries are on hold. Earlier in this payment’s '
                                   'batch: {accepted_feedings} command(s) accepted and '
                                   '{funding_cycles} CyberHerd funding transfer(s) completed. '
                                   'Physical food delivery is not confirmed.',
                              '3': '🐐 We’re holding the next headbutt while the latest feeder '
                                   'request gets checked. Its outcome is unclear. Before this '
                                   'request: {accepted_feedings} accepted command(s) and '
                                   '{funding_cycles} completed CyberHerd funding transfer(s). '
                                   'Physical food delivery is unconfirmed.',
                              '4': '🐐 The latest feeder command left us guessing. It needs a check '
                                   'before another attempt. So far this payment has '
                                   '{accepted_feedings} earlier accepted command(s) and '
                                   '{funding_cycles} completed CyberHerd funding transfer(s). We '
                                   'can’t confirm physical food delivery.',
                              '5': '🐐 A quick check is needed at the trough: the latest feeder '
                                   'command’s outcome is unknown, and automatic replay is stopped. '
                                   'Earlier totals: {accepted_feedings} command(s) accepted and '
                                   '{funding_cycles} CyberHerd funding transfer(s) completed. '
                                   'Physical food delivery is not confirmed.'},
 'member_thread': {'1': '🐐 {name}, here’s your own corner of the CyberHerd trough for this '
                        'membership cycle. Watch this thread for your treat updates.',
                   '2': '🐐 A little CyberHerd space for {name}! Your treat updates for this '
                        'membership cycle will gather here.',
                   '3': '🐐 {name}, keep an eye on this spot at the trough. This is your CyberHerd '
                        'member thread for the current membership cycle.',
                   '4': '🐐 This thread belongs to {name}’s CyberHerd adventures this membership '
                        'cycle. Your treat updates will show up here.',
                   '5': '🐐 Your CyberHerd noticeboard is ready, {name}. Treat updates for this '
                        'membership cycle will appear in this thread.'},
 'cyber_herd_space_open': {'1': 'There’s space at the trough: {active_members}/{max_members} '
                                'places filled, with {spots_remaining} open. A first like or '
                                'repost can join while a place is open.',
                           '2': 'The herd has {spots_remaining} open '
                                'place(s)—{active_members}/{max_members} filled. A first like or '
                                'repost can join while there’s space.',
                           '3': 'A little room remains in the herd: {active_members}/{max_members} '
                                'places filled · {spots_remaining} open. A first like or repost '
                                'can join an open place.',
                           '4': 'Places at the trough: {active_members}/{max_members} filled, '
                                '{spots_remaining} open. First likes and reposts can join while '
                                'space remains.',
                           '5': 'The trough isn’t full yet: {active_members}/{max_members} places '
                                'filled · {spots_remaining} open. A first like or repost can join '
                                'while a place is open.'},
 'cyber_herd_space_full': {'1': 'The trough is full: {active_members}/{max_members} places filled. '
                                'Qualifying zaps can headbutt; reposts can challenge eligible '
                                'social-only members. Likes cannot headbutt.',
                           '2': 'All {max_members} herd places are occupied '
                                '({active_members}/{max_members}). Qualifying zaps can challenge '
                                'members, and reposts can challenge eligible social-only members. '
                                'Likes cannot headbutt.',
                           '3': 'A full house at the trough: {active_members}/{max_members} places '
                                'filled. A qualifying zap can challenge a member; a repost can '
                                'challenge an eligible social-only member. A like cannot headbutt.',
                           '4': 'No open herd places right now: {active_members}/{max_members} '
                                'filled. Qualifying zaps and eligible repost headbutts can '
                                'challenge for a place. Likes cannot headbutt.',
                           '5': 'The herd has filled its places: {active_members}/{max_members}. '
                                'Qualifying zaps can challenge members; reposts can challenge '
                                'eligible social-only members. Likes need an open place and cannot '
                                'headbutt.'},
 'feeder_batch_summary': {'2': 'This payment’s menu: {feedings} feeder activation(s) and '
                               '{payout_cycles} CyberHerd payout cycle(s).',
                          '3': 'The payment funds {feedings} feeder activation(s), alongside '
                               '{payout_cycles} CyberHerd payout cycle(s).',
                          '4': 'Planned for this payment: {feedings} feeder activation(s) · '
                               '{payout_cycles} CyberHerd payout cycle(s).',
                          '5': 'From this payment’s treat bucket: funding for {feedings} feeder '
                               'activation(s) and {payout_cycles} CyberHerd payout cycle(s).'},
 'repost_hint': {'3': 'A first repost this membership cycle adds 3 points. It could help you reach '
                      'a bigger bite next time. 🐐',
                 '4': 'Still room to boost your score: your first repost this membership cycle is '
                      'worth 3 points. 🐐',
                 '5': 'Fancy a little more weight at the trough? A first repost this membership '
                      'cycle adds 3 points. 🐐'},
 'cyber_herd_zap_request': {'1': '🐐 A little CyberHerd treat for {name}: {new_amount:g} sats.',
                            '2': '🐐 From the CyberHerd treat bucket to {name}: {new_amount:g} '
                                 'sats.',
                            '3': '🐐 A share of the CyberHerd snacks for {name}: {new_amount:g} '
                                 'sats.',
                            '4': '🐐 CyberHerd snack time for {name}: {new_amount:g} sats.',
                            '5': '🐐 A bite from the CyberHerd trough for {name}: {new_amount:g} '
                                 'sats.'},
 'cyber_herd_interaction_score': {'1': 'Points added by this interaction: {earned_points}.',
                                  '2': 'This bit of support contributed {earned_points} points.',
                                  '3': 'This interaction’s contribution to your score: '
                                       '{earned_points} points.'},
 'cyber_herd_unadmitted_score': {'1': 'No membership points or share were earned by this attempt. '
                                      'Qualifying likes and reposts can still count after a later '
                                      'qualifying join.',
                                 '2': 'This attempt hasn’t earned a membership score or share. A '
                                      'later qualifying join can bring your qualifying likes and '
                                      'reposts into the tally.',
                                 '3': 'This attempt didn’t earn membership points or a share. '
                                      'Qualifying social support can contribute after a later '
                                      'qualifying join.'}}

LEGACY_UNCERTAIN_FEEDER_MESSAGE = "🐐 The latest feeder command's outcome is uncertain. Automatic replay is paused for operator reconciliation. Before this request: {accepted_feedings} command(s) accepted and {funding_cycles} CyberHerd funding transfer(s) completed. Physical food delivery is not confirmed."

for _category, _variants in MESSAGE_VARIATIONS.items():
    SEED_DEFAULTS[_category].update(_variants)


EVENING_PAUSE_TEMPLATES = {
    "0": "🐐 The feeder is resting for the evening while the goats head out to forage. The stream is signing off for the night; we’ll be back when the sun comes up!",
    "1": "🐐 Evening browsing calls! The goats are off to forage, the feeder is paused, and the stream is winding down for the night. See you when the sun comes up.",
    "2": "🐐 Bushes and branches are on tonight’s menu. The goats are heading out to forage while the feeder and stream rest until morning. Zaps are still welcome!",
    "3": "🐐 Time for an evening wander and a few leafy bites. The feeder is paused and the stream is signing off for the night. We’ll see you in the sunshine!",
    "4": "🐐 The goats are trading feeder snacks for evening forage. The feeder is paused and the stream is closing for the night; back when the sun comes up.",
    "5": "🐐 That’s our cue to browse! The goats are heading out to forage, and the feeder and stream are settling down for the night. Catch us again in the morning.",
    "6": "🐐 The feeder is taking its evening rest while the goats go foraging. The stream is signing off until sunrise. Zaps can still arrive while we’re away!",
    "7": "🐐 A few more leaves before bedtime! The goats are off to forage, the feeder is paused, and the stream is wrapping up for the night. Back with the morning sun.",
}
STREAM_CHAT_NOTICES["feeder_requests_paused_night"] = EVENING_PAUSE_TEMPLATES
SEED_DEFAULTS["feeder_requests_paused_night"] = EVENING_PAUSE_TEMPLATES
