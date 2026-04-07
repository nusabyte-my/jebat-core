#!/usr/bin/env node
import { runCli } from "../lib/cli.js";

await runCli(process.argv.slice(2));
