#!/bin/bash
case $AWS_PROFILE in
	mus)
		echo "Configuring for MUS production"
		export MakurspaceEnv="makurspace"
		export MakurspaceStaticAssets="makurspace-static-assets"
		echo 'default_bucket = "makurspace-static-assets"' > hyperspace/profile.py
		;;
	musint)
		echo "Configuring for MUS internal production"
		export MakurspaceEnv="makurspace-int"
		export MakurspaceStaticAssets="makurspace-int-static-assets"
		echo 'default_bucket = "makurspace-int-static-assets"' > hyperspace/profile.py
		;;
	musdev)
		echo "Configuring for MUS development"
		export MakurspaceEnv="makurspace-dev"
		export MakurspaceStaticAssets="makurspace-dev-static-assets"
		echo 'default_bucket = "makurspace-dev-static-assets"' > hyperspace/profile.py
		;;
esac
