import os, subprocess, sys, unittest

MINT = "GPx5APBduaoYaG1jrqYNM81GDGgLyLWev9My4mmipump"
EXPECT_SIG = "2WXTx543UZkUwDaFJpTePTgKxjDQ5c3gFBx6RDL7EnnsXfrPL8LYiBdmx4eZB3pPaYSPrSsuF2BgWPmH7hyaEWNL"
EXPECT_SIGNER = "GLf2JhxRfSuDVnRRE7TssRN2LKDvW6Afoqfq3d1c9uCJ"
EXPECT_TIME = "2026-08-29 19:14:38"


class TestReconGenesis(unittest.TestCase):
    def test_high_volume_mint_genesis(self):
        if not os.environ.get("SOLANA_RPC"):
            self.skipTest("SOLANA_RPC not set — this test requires live RPC")
        out = subprocess.check_output(
            [sys.executable, "scripts/recon_token.py", MINT], text=True)
        self.assertIn(EXPECT_SIG, out, "wrong genesis signature")
        self.assertIn(EXPECT_SIGNER, out, "wrong genesis signer/deployer")
        self.assertIn(EXPECT_TIME, out, "wrong creation time")


if __name__ == "__main__":
    unittest.main()
