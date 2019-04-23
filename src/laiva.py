from datetime import datetime, timedelta
from math import floor

from time_util import as_helsinki, as_utc, to_utc


ALLOWED_CHANNELS = ['359308335184609281', '141649840923869184', '244452088279465985']

def register(client):
    return {
        "laiva": cmd_laiva,
        "laivalle": cmd_laiva,
    }
memes = ["1GAYBN9wUUDEzP7rpJyaQuuApC5sqXMUJ",
"1UuKzL4fG4CZ8u4andG68oVuBUrXA90YQ",
"1ojerhCIlhtmEwYENfWenTvJs-4wDBDK6",
"1tI-aOybawfKF06RA5X5y_fC9te9DdqOB",
"1vpHYCV3fRnrmuxPm7igwz9t1eDt8O-CZ",
"1JOC7W8EK78YR3Y2vMGDJas1k8ME9DAs_",
"16RulYbH2eYHsVrosQ8-wgjyEjS5vSEtN",
"13CNvEIWfPO27jfjUq4opHSMEDTY94s9f",
"1_aPxGbNjBBiJX-xVDTMgC3HnGVbfQyeu",
"1AESsC1sVdNiakh7n_RYw_itfiWeFvcS-",
"13dGXgC86r-1HiIPQUSEjnkFSP_FLsHgF",
"1x3g3PnlZrFUC1QKzCnUpNJiYk2bE088P",
"1ywlioregx6TSGfCMeDgSWr-siKeHQJXx",
"1SBbrtxoXh6XKyYGFh6NjFbVjotIz9ANv",
"1dUhgsbqPYWaorBCZ7Jzj789FHHSE4l_T",
"1NcpSPJIshtrciamXyILY9WGfxXFLCNXr",
"14kpFhpcg8FjjwdgeXQxKjsroX2nizYO8",
"1cMElyjBA_GvExSrE-mAV5M2OhPogX5lf",
"1QOS6mzlyNcFtT9lqYOuPMm5-GpyHfd9R",
"1ysxSA2xvo8j_1uDUKHm0OaR7QSqcdhfx",
"198JuMd6BwFXK7aGIWvBP4eJAG0TbHJTY",
"1RWzfSH8tddVSBtwVV-BpJ5b4PfGbrHns",
"1JQGn-lAd4NppUZC-Ict6cq0Q6bBDKjRx",
"1KUchDNCG0G9TVnMrFteFBGvLxFJYmUiZ",
"1lL9sTrhkRppxhfpE_fGhXmJM3bROXlnP",
"1FX1Fg2ud3PNtPhFML-jsnmcJpliNpmc8",
"17TxKU3p9TpQ3uvWNeNke9AsO8eiAh5cp",
"1mDY_Pfrl-c2vkc4Kavfs2hQEjpJ55wfB",
"159tFbGOdu9zSX_l9MmPp-kUAApzdKSGo",
"1NQG972R21hmkDY4xQ357iJkxHUX1yU3l",
"18V--ier1zeQ5P-usBD4bterJdinEXeCD",
"1DOkFPNUUw7o-mOuhr7iQypGmc6Q5FR0Y",
"1XURbQ4hyqJxV64mCll-aYLiagB8ivq1d",
"18Lhan9E-mDAr1cSFZltyG5Ua0lr8cmei",
"1PjDjzjXR2goSA0zB_qZX-oGiMB4Kvdpd",
"16rsUFsNvKDprAGu5k9IwLsrGFedCdUu9",
"1A_wef3gTctmWv_AHWjPcEDGW8v1ptqg_",
"1uARMav7X4aMU3vyFelNkOn_E-j23okdJ",
"1y7kRqpbrS5dqivNJQKi-mZXi_fT_M7Ld",
"17jAsOQSXrjh1lNhclGmCN55GOtz0nULo",
"1_P-i7tDrIwm_jz99Nk2mgXiXo5wOb-1A",
"1x2vruUjzKI1_pNvc-pgM8oyafGjBgCvA",
"1QZam4mSPx0oXXHM9__ZXLCmEms22vy1h",
"1nDKWz7dWfDLBpleiBgJNutsONHVOK5Jc",
"1gmvasMXnZpo6FjDcxhmtyXy1O79tJeHZ",
"1qIO5EdDTdcs-dIcnrxNqJ_0de3NjDJgx",
"1eGwPWEDZhVELFt5-6XmlBqAQLZD8-zaC",
"1l-2UoQIb8R3PaG8-MvXn3MBo-0SDbEWb",
"1kjlpr3eiPLdInB1lhVAypdOIZnhmb1Nw",
"1eCNTEbTXSZkZWHC16Z24rIVYQ0mgjhoV",
"1jtbRpgtpY7P6S19cyFvQuFX7T3l2od9o",
"1atj4gWtcNvB8b2Sr7lDusGub8gqT-XbI",
"1bD-PuWn8YJbuZ1A69TfWCvaBdcdPiwRp",
"1DVX72wG55ATGHwNkCxf9qMC-Bs9nI44h",
"1K8Z8Qwd-n38Ruh2Dd397ZNz_a9LaujqE",
"1QVz7hcwZhYefYzJXHsL2T7HuNNskVT6n",
"1Q7PK3jq2IrQVI3n7vM4NT4zo1wbk2rtd",
"1jJpahqR4HRV506Y158mGSiixPKSWnpnO",
"1BXsodl91TIYjZBARMxvPksgFRhw__3dW",
"1cwpiPkph-ghD_b2crCVygB-fwY5LY4Fj",
"1-VK8ORiNrk_nIbfMY0IhopFu-UoUEjnp",
"12Ac0nfoX2sMrjfQhYK6V6ahfAUYFdEy3",
"1o1QpzJKCapSvnxd8YxjmjcVXk8OKPfn6",
"1vS2qw-RaTGzRCiDGPWGvHj8JdlCAQ_Mv",
"1n2vqsOrIi003wxmVMxXEgSU5maEmi6Ij",
"1_lNPAc4l2kCdIC9l05qCcr1S2HovynHY",
"1gU19NIpZIuUxifnVGVjAeti_S-meI_Dq",
"1K5PmnTDF9jYW3HwqnTq81ZCH8BMgyhD0",
"1ZBGR9LrwZJXjizQb9NPtyKkc32FjvjoP",
"10KMwKVCOWHGw89aBAYeADH_BP0Quuz3c",
"1rA4pxn6Abcr8ynBFtbMsn_2hYYktzwH6",
"1PDmlXWZYQfz_uVFOS-uD_JbqGi2PbsVo",
"1m8PEyFwTMXLkCabpMWxviizBebHjrllW",
"1lCkyqnggmKULxHGKTaiNZkmxU7rdzx9h",
"1zM1z86nCgx3UXOgGYOfM0Jn42SrG8M8C",
"1TlOg9IBn8zOqFz_WI1nuKDNUsFkU1ZBE",
"1anDGr0sv_k8NaQBqrka8sPcfO-a9N1k4",
"1rJA55uZh8m9Zn2sOa1pxl0XHP0oycj11",
"1Jh6bUw0aobwSV9aSJlfmyhSAYNhE6IpR",
"1OKJj0J7rTHBU4hhv_xuSW4AKWOWrbLwC",
"1NSbwIZG02qVH4DpyAxz0IY75CymCw6FD",
"15_dSkubHs9EKvOHpfSQiGWR0tSg56ZI8",
"1An9C-NBaGtyo-CumCtpZ3u0P4aInbcoB",
"1Hz7fGaQJbl1AqmLoOj37SuvU7CbXG0ts",
"1JpseTz7oq6rvM00eO50zIUoSwE8WQM7K",
"1dSVUJoF5NfCnaQ_eWF2p87K4002OJ0wl",
"1a2CCCduhyxLSK5-DH5bFlRtW1eIaE3c7",
"1uoSgEYH-ynl74y3Szccyp0Gf8ZOOw00k"]

async def get_laiva_meme_of_the_day(day):
    return "https://drive.google.com/file/d/" + memes[day] + "/view?usp=sharing"

async def cmd_laiva(client, message, _):

    if message.channel.id not in ALLOWED_CHANNELS:
        await client.send_message(message.channel, "You cannot use this command here.")
        return

    theme = "The laiva to start a new generation of laivas"
    laiva = to_utc(as_helsinki(datetime(2019, 6, 7, 17, 0)))
    laivaover = to_utc(as_helsinki(datetime(2019, 6, 9, 10, 30)))

    now = as_utc(datetime.now())


    if (laiva < now) and (laivaover > now):
        await client.send_message(message.channel, "Laiva is currently happening!!")
        return

    if ((laivaover + timedelta(days=1)) < now) and laiva < now:
        time_ago = delta_to_str(now - laivaover)
        await client.send_message(message.channel, f"**Last laiva ended:** {time_ago} ago, **next laiva:** TBA.")
        return

    if laivaover < now:
        await client.send_message(message.channel, "Laiva is already over, but paha olo remains.")
        return

    time_left = delta_to_str(laiva - now)
    msg = f"Time left until '{theme}': {time_left}!!"
    if (laiva - timedelta(days=len(memes)-1)) < now:
        msg += "\n**Laiva meme of the day**:\n%s" % await get_laiva_meme_of_the_day((laiva - now).days)
    await client.send_message(message.channel, msg)

def delta_to_str(delta):
    return "{0} days, {1} hours, {2} minutes, {3} seconds".format(*delta_to_tuple(delta))

def delta_to_tuple(delta):
    days = delta.days
    s = delta.seconds
    seconds = s % 60
    m = floor((s - seconds) / 60)
    minutes = m % 60
    h = floor((m - minutes) / 60)
    hours = h
    return (days, hours, minutes, seconds)
