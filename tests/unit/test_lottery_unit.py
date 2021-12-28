import time
from brownie.network import account
import pytest
from brownie import Lottery, accounts, network, config, exceptions
from toolz.itertoolz import get
from web3 import Web3
from scripts.deploy_lottery import deploy_lottery, enter_lottery
from scripts.helpful_scripts import (
    LOCAL_DEV_ENVIRONMENTS,
    get_account,
    fund_with_link,
    get_contract,
)


def test_get_entrance_fee():
    if network.show_active() not in LOCAL_DEV_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    deploy_lottery()
    lottery = Lottery[-1]
    # Act
    entrance_fee = lottery.getEntranceFee()
    ## Assuming $4000eth/usd (in development) and entrance fee $50 -> 50/4000 = 0.0125 eth
    expected_entrance_fee = Web3.toWei((50 / 4000), "ether")
    # Assert
    # assert entrance_fee >= Web3.toWei(0.012, "ether") and entrance_fee < Web3.toWei(
    #     0.013, "ether"
    assert entrance_fee == expected_entrance_fee


def test_cant_enter_unless_started():
    if network.show_active() not in LOCAL_DEV_ENVIRONMENTS:
        pytest.skip()
    deploy_lottery()
    lottery = Lottery[-1]
    account = get_account()
    entrance_fee = lottery.getEntranceFee()
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from": account, "value": entrance_fee})
        # enter_lottery()


def test_can_start_and_enter_lottery():
    if network.show_active() not in LOCAL_DEV_ENVIRONMENTS:
        pytest.skip()
    # arrange
    account = get_account()
    deploy_lottery()
    lottery = Lottery[-1]
    entrance_fee = lottery.getEntranceFee()
    # Act
    start_tx = lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": entrance_fee})
    # Assert
    assert lottery.players(0) == account


def test_can_end_lottery():
    if network.show_active() not in LOCAL_DEV_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    deploy_lottery()
    account = get_account()
    lottery = Lottery[-1]
    start_tx = lottery.startLottery({"from": account})
    start_tx.wait(1)
    fund_tx = fund_with_link(lottery.address)
    fund_tx.wait(1)
    end_tx = lottery.endLottery({"from": account})
    end_tx.wait(1)
    print(lottery.lottery_state())
    # Act
    # Assert
    assert lottery.lottery_state() != 0  # 0 = OPEN, 1 = calculating, 2 = closed


def test_and_pick_winner_correctly():
    if network.show_active() not in LOCAL_DEV_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    deploy_lottery()
    lottery = Lottery[-1]
    account = get_account()
    start_tx = lottery.startLottery({"from": account})
    start_tx.wait(1)
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=1), "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=2), "value": lottery.getEntranceFee()})
    original_balance = account.balance()
    # Act
    fund_with_link(lottery.address)
    end_tx = lottery.endLottery({"from": account})
    request_id = end_tx.events["RequestedRandomness"]["requestId"]
    static_random_number = 777
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, static_random_number, lottery.address, {"from": account}
    )
    # since we have 3 entries = players[0,1,2] and 777%3 = 0 -> winner = account
    # end_tx.wait(1)
    # time.sleep(10)
    winnings = lottery.getEntranceFee() * 3
    # Assert
    print(lottery.lottery_state())
    assert lottery.recentWinner() == account.address
    assert lottery.randomness() == 777
    assert lottery.balance == 0
    assert account.balance() == original_balance + winnings
