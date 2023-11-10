FROM ruby:3.1.3

WORKDIR /aihelper

COPY Gemfile /aihelper/Gemfile
COPY Gemfile.lock /aihelper/Gemfile.lock

RUN bundle install

COPY . /aihelper

EXPOSE 4567

# CMD ["ruby", "aihelper.rb"]
# CMD ["irb"]
