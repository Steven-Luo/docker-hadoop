# -*- mode: ruby -*-
# vi: set ft=ruby :
#
require 'json'

Vagrant.configure("2") do |config|
  config.vm.box = "raring"
  config.vm.box_url = "http://cloud-images.ubuntu.com/raring/current/raring-server-cloudimg-vagrant-amd64-disk1.box"
  config.vm.network "forwarded_port", guest: 5000, host: 5000

  config.vm.provider "virtualbox" do |v|
    v.customize ["modifyvm", :id,  "--memory", 8192]
  end

  # Check if a vm has been provisioned yet
  if File.exists?".vagrant_file"
    vagrant_file = JSON.load(IO.read('.vagrant_file'))
  end
  if vagrant_file.nil? or !vagrant_file['active'].has_key?('default')
    # I broke out each command here so we can see exactly what occurs

    # We're gonna use this a few times
    apt_update                = "apt-get update;"

    # Shortcut in case we need it
    restart                   = "shutdown -r +1;"

    # Install aufs
    aufs_supp                 = "apt-get install linux-image-extra-`uname -r` dkms -y;"

    # Add the repo key so we can grab 0.6
    add_docker_repo_key       = "sudo sh -c \"curl http://get.docker.io/gpg | apt-key add -\";"

    # Add the repo for the Docker packages
    add_docker_repo           = "sudo sh -c \"echo deb https://get.docker.io/ubuntu docker main > /etc/apt/sources.list.d/docker.list\";"

    # Install Docker
    install_docker            = "apt-get install -q -y --force-yes lxc-docker;"

    # Put it all together,
    icmd = "#{apt_update} "\
           "#{aufs_supp} "\
           "#{add_docker_repo} "\
           "#{add_docker_repo_key}"\
           "#{apt_update} "\
           "#{install_docker}"

    # And run it.
    config.vm.provision :shell, :inline => icmd
  end
end

#hola