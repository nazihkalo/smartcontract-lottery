from brownie import Lottery, network, config
from brownie.network import account
from scripts.helpful_scripts import (
    get_account,
    LOCAL_DEV_ENVIRONMENTS,
    FORKED_MAINNET_ENVIRONMENTS,
    get_contract,
    fund_with_link,
)
import time


def deploy_lottery():
    account = get_account()

    lottery = Lottery.deploy(
        get_contract("eth_usd_price_feed").address,
        get_contract("vrf_coordinator").address,
        get_contract("link_token").address,
        config["networks"][network.show_active()]["fee"],
        config["networks"][network.show_active()]["keyhash"],
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify", False),
    )
    print("Deployed Lottery!")


def start_lottery():
    account = get_account()
    lottery = Lottery[-1]
    start_tx = lottery.startLottery({"from": account})
    start_tx.wait(1)
    print("Lottery started!")


def enter_lottery():
    account = get_account()
    lottery = Lottery[-1]
    value = lottery.getEntranceFee() + 10000000
    enter_tx = lottery.enter({"from": account, "value": value})
    enter_tx.wait(1)
    print("You entered the lottery!")


def end_lottery():
    account = get_account()
    lottery = Lottery[-1]
    # fund the contract
    # then end the lottery
    fund_tx = fund_with_link(lottery.address)
    fund_tx.wait(1)
    end_tx = lottery.endLottery({"from": account})
    end_tx.wait(1)
    time.sleep(60)
    print(f"{lottery.recentWinner()} is the winner!")


def main():
    deploy_lottery()
    start_lottery()
    enter_lottery()
    end_lottery()
