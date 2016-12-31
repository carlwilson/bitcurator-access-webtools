#-*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

    # Uncomment this to use 14.04LTS
    # config.vm.box = "ubuntu/trusty64"

    # Uncomment this to use 16.04LTS
    config.vm.box = "bento/ubuntu-16.04"

    # Set the box host-name
    # config.vm.hostname = "ubuntu-xenial"

    # Run the provisioning script
    config.vm.provision :shell, :path => "./provision/bootstrap.sh"

    # Run the server start script
    # config.vm.provision :shell, :path => "./provision/servstart.sh",
    # run: "always"

    # Run the Celery daemon start script
    config.vm.provision :shell, :path => "./provision/taskserv.sh",
     run: "always"

    # Configure synced folder
    # config.vm.synced_folder "", "/vagrant"

    # Port forward HTTP (80) to host 2020
    config.vm.network :forwarded_port, :host => 8080, :guest => 80

    config.vm.provider :virtualbox do |vb|
      vb.name = "bca-webtools-0.7.6"
      vb.memory = 4096
      vb.cpus = 2
    end
end
