#!/bin/bash
case $AWS_PROFILE in
	mus)
		echo "Configuring for MUS production"
		export MakurpsaceStaticAssets="MakurpsaceStaticAssets"
		;;
	musint)
		echo "Configuring for MUS internal production"
		export MakurpsaceStaticAssets="makurspace-int-static-assets"
		;;
	musdev)
		echo "Configuring for MUS development"
		export MakurpsaceStaticAssets="makurspace-dev-static-assets"
		;;
esac
