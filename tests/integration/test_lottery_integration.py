import time
from brownie import network, Lottery
import pytest
from scripts.deploy_lottery import deploy_lottery

from scripts.helpful_scripts import LOCAL_DEV_ENVIRONMENTS, fund_with_link, get_account


def test_can_pick_winner():
    if network.show_active() in LOCAL_DEV_ENVIRONMENTS:
        pytest.skip()
    deploy_lottery()
    lottery = Lottery[-1]
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    fund_with_link(lottery.address)
    end_txn = lottery.endLottery({"from": account})
    time.sleep(60)

    assert len(lottery.recentWinner()) > 0
    assert lottery.recentWinner() == account.address
    assert lottery.balance() == 0
